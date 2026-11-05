"""complexity: estimate the growth class from deterministic instruction counts.

Method (callgrind): run the program on the sizes in params["sizes"] (stdin built
by a seeded generator), count executed instructions with valgrind callgrind and
fit I(n) = a + b * n^k by least squares (a absorbs the start-up cost, k is the
growth exponent, found by a grid search; needs >= 3 sizes). k maps to a class.
A program that does not finish one of the sizes within timeout_s under callgrind
scores 0, because it is too slow for the required class. Fallback (no valgrind, a
crash during measurement, or growth too small to measure): static loop-nesting
depth, reported as low confidence.

params: required ("O(1)"...), sizes, generator ("scalar"|"single_n"|"array"|"array_with_target"|
        "repeated_char"|"path_graph"),
        method ("auto"|"callgrind"|"static"), seed, growth_threshold (0.05),
        timeout_s (30), profile (false: add valgrind/perf profile to the evidence)
Score: 1.0 if the estimate is within the required class, 0.5 one class above, else 0.
"""
import random
import re

from agent import csource, profiling, sandbox
from agent.counter_tests import SIZE_GENERATORS
from agent.registry import register, AnalyzerResult

try:
    import numpy as _np
except ImportError:          # NumPy is optional; a pure-Python fit gives the same line
    _np = None

CLASSES = ["O(1)", "O(log n)", "O(n)", "O(n log n)", "O(n^2)", "O(n^3)"]


def parse_class(text: str) -> int:
    t = re.sub(r"\s+", "", str(text).lower()).replace("²", "^2").replace("³", "^3")
    t = t.replace("n2", "n^2").replace("n3", "n^3").replace("^^", "^")
    table = {"o(1)": 0, "o(logn)": 1, "o(n)": 2, "o(nlogn)": 3, "o(n^2)": 4, "o(n^3)": 5}
    if t not in table:
        raise ValueError(f"unknown complexity class '{text}'; use one of {CLASSES}")
    return table[t]


def class_from_slope(k: float) -> int:
    for limit, idx in ((0.2, 0), (0.6, 1), (1.07, 2), (1.5, 3), (2.5, 4)):
        if k < limit:
            return idx
    return 5


def _polyfit(xs, ys):
    if _np is not None:
        m, b = _np.polyfit(xs, ys, 1)
        return float(m), float(b)
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    m = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return m, my - m * mx


def fit_power(sizes, counts):
    """Fit counts ~ a + b * n^k. Returns (k, r_squared) or (None, None).
    The grid search over k (step 0.01) is deterministic."""
    if len(sizes) < 3 or counts[-1] <= counts[0]:
        return None, None
    mean = sum(counts) / len(counts)
    ss_tot = sum((c - mean) ** 2 for c in counts)
    best = None
    for step in range(1, 401):
        k = step / 100
        xs = [n ** k for n in sizes]
        top = max(xs)
        xs = [x / top for x in xs]
        m, b = _polyfit(xs, counts)
        if m <= 0:
            continue
        sse = sum((c - (m * x + b)) ** 2 for x, c in zip(xs, counts))
        if best is None or sse < best[0] - 1e-9 * max(ss_tot, 1.0):
            best = (sse, k)
    if best is None:
        return None, None
    r2 = 1.0 if ss_tot == 0 else 1 - best[0] / ss_tot
    return best[1], r2


# ------------------------------------------------------------ static fallback
def static_estimate(src: str) -> dict:
    """Loop-nesting depth (and recursion) from the comment-free source."""
    s = csource.blank_comments_and_strings(src)
    toks = re.findall(r"[A-Za-z_]\w*|\S", s)
    n, i = len(toks), 0
    scopes, unbraced, skip_while, depth_max = [], [], False, 0

    def depth():
        return sum(1 for k in scopes if k in ("loop", "do")) + len(unbraced)

    def skip_header(j):          # j at "(": return index after the matching ")"
        d = 0
        while j < n:
            d += (toks[j] == "(") - (toks[j] == ")")
            j += 1
            if d == 0:
                break
        return j

    while i < n:
        t = toks[i]
        if t in ("for", "while") and i + 1 < n and toks[i + 1] == "(":
            i = skip_header(i + 1)
            if t == "while" and skip_while:
                skip_while = False
                continue
            if i < n and toks[i] == "{":
                scopes.append("loop")
                i += 1
            else:
                unbraced.append(len(scopes))
            depth_max = max(depth_max, depth())
            continue
        if t == "do" and i + 1 < n and toks[i + 1] == "{":
            scopes.append("do")
            depth_max = max(depth_max, depth())
            i += 2
            continue
        if t == "{":
            scopes.append("block")
        elif t == "}" and scopes:
            if scopes.pop() == "do":
                skip_while = True
            while unbraced and unbraced[-1] == len(scopes):
                unbraced.pop()
        elif t == ";":
            while unbraced and unbraced[-1] == len(scopes):
                unbraced.pop()
        i += 1
    recursion = False
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*\([^;{}()]*\)\s*\{", s):
        name = m.group(1)
        if name in ("if", "for", "while", "switch", "return", "sizeof"):
            continue
        j, d = m.end(), 1
        while j < len(s) and d:
            d += (s[j] == "{") - (s[j] == "}")
            j += 1
        if re.search(rf"\b{name}\s*\(", s[m.end():j]):
            recursion = True
    cls = {0: 0, 1: 2, 2: 4, 3: 5}.get(depth_max, 5)
    if recursion:
        cls = max(cls, 2)
    return {"loop_depth": depth_max, "recursion": recursion, "class": cls}


def _measure(ctx, sizes, gen, seed, timeout):
    """Returns (counts, note, timed_out)."""
    counts = []
    for n in sizes:
        data = gen(n, random.Random(seed * 1000003 + n))
        c, outcome = profiling.callgrind_run(ctx.sandbox, ctx.binary_path, data, ctx.workdir, timeout)
        if outcome == sandbox.TIMEOUT:
            return None, f"the program did not finish within {timeout:g} s at size {n}", True
        if c is None or outcome != sandbox.OK:
            return None, f"the program could not be measured at size {n} ({outcome or 'no count'})", False
        counts.append(c)
    return counts, None, False


@register("complexity_estimator", needs_execution=True)
class ComplexityEstimator:
    def run(self, ctx):
        p = ctx.params
        required = parse_class(p.get("required", "O(1)"))
        sizes = sorted({int(x) for x in p.get("sizes", [1, 10, 100])})
        if len(sizes) < 2:
            raise ValueError("complexity sizes need at least two different values")
        gname = p.get("generator", "scalar")
        if gname not in SIZE_GENERATORS:
            raise ValueError(f"unknown size generator '{gname}'; choose from {sorted(SIZE_GENERATORS)}")
        method = p.get("method", "auto")
        seed = int(p.get("seed", 12345))
        static = static_estimate(ctx.source_path.read_text(encoding="utf-8", errors="replace"))
        ev = {"required": CLASSES[required], "sizes": sizes, "generator": gname}
        counts, note, timed_out = None, None, False
        if method in ("auto", "callgrind"):
            if profiling.have("valgrind"):
                counts, note, timed_out = _measure(ctx, sizes, SIZE_GENERATORS[gname], seed,
                                                   float(p.get("timeout_s", 30)))
            elif method == "callgrind":
                raise RuntimeError("valgrind is not installed (sudo apt install valgrind)")
            else:
                note = "valgrind is not installed"
        if timed_out:
            ev.update({"method": "callgrind", "estimated": "did not finish", "note": note})
            return AnalyzerResult(score=0.0, evidence=ev,
                                  feedback=f"Too slow: {note}; required {CLASSES[required]}",
                                  suggestions=["The program is far slower than required: look for repeated "
                                               "work, such as recursion that recomputes the same values."])
        est, how = None, "static_loop_depth"
        if counts:
            growth = (counts[-1] - counts[0]) / counts[0] if counts[0] else 0.0
            slope, r2 = fit_power(sizes, counts)
            ev.update({"instructions": counts, "growth": round(growth, 4)})
            if len(sizes) < 3:
                note = "at least 3 sizes are needed for a fit. Static estimate used."
            elif growth < float(p.get("growth_threshold", 0.05)) or slope is None:
                if static["class"] > 0:
                    note = "growth too small to measure (start-up cost dominates); use larger sizes. " \
                           "Static estimate used."
                else:
                    est, how = 0, "callgrind"
                    ev["exponent"] = 0.0
            else:
                est, how = class_from_slope(slope), "callgrind"
                ev["exponent"] = round(slope, 2)
                if r2 is not None:
                    ev["r_squared"] = round(r2, 4)
        if est is None:
            est = static["class"]
            ev.update({"loop_depth": static["loop_depth"], "recursion": static["recursion"],
                       "confidence": "low"})
            if note:
                ev["note"] = note
        ev.update({"method": how, "estimated": CLASSES[est]})
        if p.get("profile") and ctx.binary_path:
            ev["profile"] = profiling.profile_program(
                ctx.sandbox, ctx.binary_path, SIZE_GENERATORS[gname](sizes[0], random.Random(seed)),
                ctx.workdir, use_perf=bool(p.get("perf")))
        score = 1.0 if est <= required else (0.5 if est == required + 1 else 0.0)
        fb = f"Estimated {CLASSES[est]} ({how.replace('_', ' ')}); required {CLASSES[required]}"
        sugg = []
        if est > required:
            sugg.append("The program grows faster than required: look for nested loops or repeated "
                        "work that can be done once, or a formula that replaces a loop.")
        return AnalyzerResult(score=score, evidence=ev, feedback=fb, suggestions=sugg)
