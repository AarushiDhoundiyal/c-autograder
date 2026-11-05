"""Counter-test generation: curated corner cases + seeded random inputs,
differential testing against the trusted reference solution, and a
delta-debugging minimiser that shrinks a failing input to the smallest
example. Expected outputs ALWAYS come from the reference program.

Used by analyzers/edge_case_runner.py, and runnable on its own:

    python -m agent.counter_tests samples/add_basic.c --rules rules/add_full.json \
        --count 30 --save problems/add/counter
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

INT_MAX, INT_MIN = 2**31 - 1, -2**31


# ---------------------------------------------------------------- seeding
def derive_seed(rules_hash: str, problem: str, salt: str = "") -> int:
    """Same rules + same problem -> same seed -> same extra tests."""
    return int(hashlib.sha256(f"{rules_hash}|{problem}|{salt}".encode()).hexdigest()[:8], 16)


# ------------------------------------------------- random input generators
def _two_ints(rng: random.Random, i: int) -> str:
    mode = i % 6
    if mode == 0:
        a, b = rng.randint(-100, 100), rng.randint(-100, 100)
    elif mode == 1:
        a, b = rng.randint(-10**6, 10**6), rng.randint(-10**6, 10**6)
    elif mode == 2:
        a, b = INT_MAX - rng.randint(0, 5), rng.randint(0, 10)
    elif mode == 3:
        a, b = INT_MIN + rng.randint(0, 5), -rng.randint(0, 10)
    elif mode == 4:
        a, b = rng.randint(INT_MIN, INT_MAX), rng.randint(INT_MIN, INT_MAX)
    else:
        a, b = rng.randint(2**30, INT_MAX), rng.randint(2**30, INT_MAX)
    return f"{a} {b}\n"


def _single_int(rng: random.Random, i: int) -> str:
    return f"{rng.choice([0, 1, -1, rng.randint(-1000, 1000), rng.randint(INT_MIN, INT_MAX)])}\n"


def _int_list(rng: random.Random, i: int) -> str:
    n = rng.choice([0, 1, 2, rng.randint(3, 20)])
    return f"{n}\n" + " ".join(str(rng.randint(-1000, 1000)) for _ in range(n)) + "\n"


GENERATORS = {"two_ints": _two_ints, "single_int": _single_int, "int_list": _int_list}

# size-driven generators for the complexity estimator: f(n, rng) -> stdin text
SIZE_GENERATORS = {
    "scalar": lambda n, rng: f"{n} {n}\n",
    "single_n": lambda n, rng: f"{n}\n",
    "array": lambda n, rng: f"{n}\n" + " ".join(str(rng.randint(0, 1000)) for _ in range(n)) + "\n",
}


# ------------------------------------------------------------ edge-case file
def load_edge_cases(path) -> dict:
    """Accepts {"groups": {...}, "random": {...}} or a plain {group: [inputs]} map."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "groups" not in data:
        data = {"groups": data}
    for g, items in data["groups"].items():
        if not isinstance(items, list) or not all(isinstance(x, str) for x in items):
            raise ValueError(f"edge-case group '{g}' must be a list of input strings")
    return data


def default_groups(spec: dict) -> list:
    return list(spec["groups"]) + (["random"] if "random" in spec else [])


def collect_inputs(spec: dict, group_names, seed: int, random_count=None) -> list:
    """[(group, input)] in the order of group_names (reproducible)."""
    out = []
    for g in group_names:
        if g == "random":
            r = spec.get("random")
            if not r:
                raise ValueError("group 'random' requested but the edge-case file has no 'random' section")
            gen = GENERATORS.get(r.get("generator", ""))
            if gen is None:
                raise ValueError(f"unknown random generator '{r.get('generator')}'; "
                                 f"choose from {sorted(GENERATORS)}")
            count = int(random_count if random_count is not None else r.get("count", 20))
            rng = random.Random(seed)
            out += [("random", gen(rng, i)) for i in range(count)]
        elif g in spec["groups"]:
            out += [(g, text) for text in spec["groups"][g]]
        else:
            raise ValueError(f"unknown edge-case group '{g}'; available: {default_groups(spec)}")
    return out


# --------------------------------------------------------- differential test
def _io():
    # lazy import: analyzers/__init__ imports analyzers that import this module
    from analyzers import io_tests
    return io_tests


@dataclass
class CaseResult:
    group: str
    input: str
    expected: str = ""
    got: str = ""
    ok: bool = True
    valid: bool = True        # False when the reference itself could not answer
    kind: str = ""
    note: str = ""
    why: str = ""


def show_input(s: str) -> str:
    """Readable input; falls back to repr() when whitespace itself matters."""
    t = s.strip()
    plain = s.endswith("\n") and "\r" not in s and "\t" not in s and "  " not in t and "\n" not in t
    return t if plain else repr(s)


def build_reference(sb, ref_src, workdir):
    out = Path(workdir) / "reference.bin"
    comp = sb.compile(Path(ref_src), out, ["-O2", "-std=c11"], cwd=Path(ref_src).parent)
    if not comp.ok:
        raise RuntimeError("reference solution does not compile: " + "; ".join(comp.errors[:2]))
    return out


def run_case(sb, student_bin, ref_bin, group: str, text: str, compare: str = "tokens") -> CaseResult:
    io = _io()
    ref = sb.run([ref_bin], stdin=text)
    if not ref.ok:
        return CaseResult(group, text, valid=False, note="reference could not answer this input")
    st = sb.run([student_bin], stdin=text)
    if st.ok and io.same(ref.stdout, st.stdout, compare):
        return CaseResult(group, text, ref.stdout.strip(), st.stdout.strip())
    kind, note, why = io.explain(ref.stdout, st.stdout, st, sb.time_limit_s)
    return CaseResult(group, text, ref.stdout.strip(), st.stdout.strip(), ok=False,
                      kind=kind, note=note, why=why)


def run_cases(sb, student_bin, ref_bin, cases, compare="tokens") -> list:
    return [run_case(sb, student_bin, ref_bin, g, t, compare) for g, t in cases]


# ----------------------------------------------------------------- minimiser
def _as_int(tok: str):
    return int(tok) if re.fullmatch(r"[+-]?\d+", tok) else None


def _shrinks(v: int) -> list:
    sign = 1 if v > 0 else -1
    cands = [0, sign, int(v / 2), v - sign]
    seen, out = set(), []
    for c in cands:
        if abs(c) < abs(v) and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def minimise(text: str, still_fails, budget: int = 120, drop_tokens: bool = False) -> str:
    """Delta-debugging: normalise whitespace, optionally drop tokens, push numbers
    toward zero, while still_fails(candidate) stays True. At most `budget` checks."""
    calls = 0

    def check(t: str) -> bool:
        nonlocal calls
        if calls >= budget:
            return False
        calls += 1
        return still_fails(t)

    best = text
    toks = best.split()
    if not toks:
        return best
    norm = " ".join(toks) + "\n"
    if norm != best and check(norm):
        best = norm
    toks = best.split()
    changed = True
    while changed and calls < budget:
        changed = False
        if drop_tokens:
            i = 0
            while i < len(toks) and len(toks) > 1:
                cand = toks[:i] + toks[i + 1:]
                if check(" ".join(cand) + "\n"):
                    toks, changed = cand, True
                else:
                    i += 1
        for i, t in enumerate(toks):
            v = _as_int(t)
            if v is None or v == 0:
                continue
            for c in _shrinks(v):
                cand = toks[:i] + [str(c)] + toks[i + 1:]
                if check(" ".join(cand) + "\n"):
                    toks, changed = cand, True
                    break
    return " ".join(toks) + "\n"


def generate_counter_tests(sb, student_bin, ref_bin, spec, groups, seed, compare="tokens",
                           random_count=None, minimise_first: int = 3,
                           drop_tokens: bool = False) -> tuple:
    """Returns (all CaseResults, failing counter-tests as dicts).
    The first `minimise_first` failures are shrunk to a minimal input."""
    results = run_cases(sb, student_bin, ref_bin,
                        collect_inputs(spec, groups, seed, random_count), compare)
    failing, shrunk = [], 0
    for k, r in enumerate(x for x in results if x.valid and not x.ok):
        text, orig = r.input, None
        if shrunk < minimise_first:
            shrunk += 1
            pred = lambda t: not run_case(sb, student_bin, ref_bin, r.group, t, compare).ok \
                and run_case(sb, student_bin, ref_bin, r.group, t, compare).valid
            small = minimise(r.input, pred, drop_tokens=drop_tokens)
            if small != r.input:
                text, orig = small, r.input
        final = run_case(sb, student_bin, ref_bin, r.group, text, compare)
        if final.ok or not final.valid:       # safety net: keep the original failure
            text, orig, final = r.input, None, r
        item = {"test": f"{r.group}#{k + 1}", "group": r.group, "input": show_input(text),
                "expected": final.expected, "got": final.got or "(no output)",
                "note": final.note, "why": final.why, "kind": final.kind, "_raw": text}
        if orig is not None:
            item["minimised_from"] = show_input(orig)
        failing.append(item)
    return results, failing


# ----------------------------------------------------------------------- CLI
def main(argv=None) -> int:
    import argparse
    import tempfile
    from agent import REPO_ROOT, sandbox
    from agent.rules import load_rules

    ap = argparse.ArgumentParser(description="Generate counter-tests that expose a submission's bugs")
    ap.add_argument("source")
    ap.add_argument("--rules", required=True)
    ap.add_argument("--count", type=int, default=None, help="number of random cases")
    ap.add_argument("--save", default=None, help="write failing inputs as NNN.in/NNN.out here")
    a = ap.parse_args(argv)

    rules = load_rules(a.rules)
    spec_m = next((m for m in rules.metrics if m.analyzer == "edge_case_runner"), None)
    if spec_m is None:
        print("the rules file has no edge_case_runner metric")
        return 2

    def find(p):
        for base in (Path.cwd(), rules.base_dir, REPO_ROOT):
            if (Path(base) / p).exists():
                return Path(base) / p
        return Path(p)

    sb = sandbox.Sandbox(rules.time_limit_s, rules.memory_limit_mb)
    with tempfile.TemporaryDirectory(prefix="counter_") as tmp:
        work = Path(tmp)
        src = Path(a.source).resolve()
        stu = work / "student.bin"
        comp = sb.compile(src, stu, sandbox.DEFAULT_COMPILE_FLAGS, cwd=src.parent)
        if not comp.ok:
            print("submission does not compile:", *comp.errors[:3], sep="\n  ")
            return 1
        ref = build_reference(sb, find(spec_m.params["reference"]), work)
        spec = load_edge_cases(find(spec_m.params["edge_cases_file"]))
        seed = derive_seed(rules.hash, rules.problem)
        results, failing = generate_counter_tests(sb, stu, ref, spec, default_groups(spec), seed,
                                                  random_count=a.count)
        total = sum(1 for r in results if r.valid)
        print(f"{total - len(failing)}/{total} generated cases passed (seed {seed})")
        for f in failing:
            print(f"\n[{f['test']}] INPUT: {f['input']}\n  EXPECTED: {f['expected']}\n  GOT: {f['got']}\n  WHY: {f['why']}")
        if a.save and failing:
            out = Path(a.save)
            out.mkdir(parents=True, exist_ok=True)
            for i, f in enumerate(failing, 1):
                (out / f"{i:03d}.in").write_text(f["_raw"])
                (out / f"{i:03d}.out").write_text(f["expected"] + "\n")
            print(f"\nsaved {len(failing)} counter-tests to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
