"""memory_safety: rebuild with AddressSanitizer + UndefinedBehaviorSanitizer
(+ LeakSanitizer) at -O0, run every test, parse the reports.

params: testset_dir (optional; falls back to the smoke input),
        flags (default "-fsanitize=address,undefined -g -O0")
score = max(0, 1 - 0.34 * distinct findings), a finding being (kind, source line).
No address-space limit here: ASan reserves terabytes of virtual memory.
Each finding keeps the first test input that triggered it, so the student
sees a concrete input that exposes the problem.
"""
import re
import shlex

from agent.registry import register, AnalyzerResult
from agent.testset import discover_tests

_UB = re.compile(r"(?P<file>[^\s:]+):(?P<line>\d+):\d+: runtime error: (?P<msg>.*)")
_ASAN = re.compile(r"ERROR: AddressSanitizer: (?P<kind>[\w-]+)")
_LEAK = re.compile(r"^(Direct|Indirect) leak of (?P<bytes>\d+) byte")
_LINE = lambda name: re.compile(re.escape(name) + r":(\d+)")
_ADDRESS = re.compile(r"0x[0-9a-fA-F]+")

WHY = {
    "signed-integer-overflow": "The arithmetic result does not fit in a signed int, which is undefined "
                               "behaviour in C. Use a wider type (long long) or check the range first.",
    "memory-leak": "Memory obtained with malloc/calloc is never released. Call free() on every "
                   "allocation before the program ends.",
    "null-dereference": "The program reads or writes through a null pointer. Check pointers before use.",
    "SEGV": "The program accessed invalid memory. Check pointers and array indexes.",
    "stack-overflow": "The recursion goes too deep and runs out of stack. Add or fix the base case, "
                      "or replace deep recursion with a loop.",
    "heap-buffer-overflow": "The program reads or writes past the end of a heap block. Check the allocated size.",
    "stack-buffer-overflow": "The program reads or writes past the end of a local array. Check the index range.",
    "heap-use-after-free": "The program uses memory after free(). Do not touch a pointer after freeing it.",
    "attempt-to-free": "The program frees memory that was not allocated or frees it twice.",
}


def _kind_from_ub(msg: str) -> str:
    m = msg.lower()
    for key, kind in (("signed integer overflow", "signed-integer-overflow"),
                      ("null pointer", "null-dereference"), ("division by zero", "division-by-zero"),
                      ("out of bounds", "array-out-of-bounds"), ("shift", "invalid-shift"),
                      ("uninitialized", "uninitialized-read")):
        if key in m:
            return kind
    return "undefined-behaviour"


def parse_sanitizer(stderr: str, src_name: str):
    """Return [{kind, line, message}] in order of appearance (deduplicated per run)."""
    findings, lines, find_line = [], stderr.splitlines(), _LINE(src_name)

    def first_line_after(i):
        for j in range(i, min(i + 30, len(lines))):
            if lines[j].startswith("==") and j > i:
                break
            m = find_line.search(lines[j])
            if m:
                return int(m.group(1))
        return None

    for i, ln in enumerate(lines):
        m = _UB.search(ln)
        if m:
            findings.append({"kind": _kind_from_ub(m.group("msg")), "line": int(m.group("line")),
                             "message": _ADDRESS.sub("<address>", m.group("msg").strip())})
            continue
        m = _ASAN.search(ln)
        if m:
            kind = m.group("kind")
            # the line where the stack runs out depends on the random stack layout, so it is not recorded
            line = None if kind == "stack-overflow" else first_line_after(i + 1)
            findings.append({"kind": kind, "line": line, "message": f"AddressSanitizer: {kind}"})
            continue
        m = _LEAK.match(ln.strip())
        if m:
            findings.append({"kind": "memory-leak", "line": first_line_after(i + 1),
                             "message": f"{m.group('bytes')} byte(s) leaked"})
    seen, out = set(), []
    for f in findings:
        key = (f["kind"], f["line"])
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


@register("sanitizer_run", needs_execution=True)
class SanitizerRun:
    def run(self, ctx):
        flags = shlex.split(ctx.params.get("flags", "-fsanitize=address,undefined -g -O0"))
        if not any(f.startswith("-O") for f in flags):
            flags.append("-O0")
        if not any(f.startswith("-std=") for f in flags):
            flags.append("-std=c11")
        comp = ctx.sandbox.compile(ctx.source_path, ctx.workdir / "sanitized.bin", flags,
                                   cwd=ctx.source_path.parent)
        if not comp.ok:
            raise RuntimeError("sanitizer build failed: " + (comp.errors[0] if comp.errors else comp.stderr[:120]))
        if "testset_dir" in ctx.params:
            cases = [(t.name, t.input) for t in discover_tests(ctx.resolve(ctx.params["testset_dir"]))]
        else:
            cases = [("smoke", ctx.rules.smoke_input)]
        env = {"ASAN_OPTIONS": "detect_leaks=1:color=never:symbolize=1",
               "UBSAN_OPTIONS": "print_stacktrace=0:color=never"}
        limit = ctx.time_limit_s * 3 + 2
        found, failing = {}, []
        for name, text in cases:
            r = ctx.sandbox.run([comp.output_path], stdin=text, time_limit_s=limit,
                                memory_limit_mb=None, nproc=2048, env=env)
            for f in parse_sanitizer(r.stderr, ctx.source_path.name):
                key = (f["kind"], f["line"])
                if key not in found:
                    found[key] = {**f, "test": name}
                    where = f" at line {f['line']}" if f["line"] else ""
                    failing.append({"test": name, "input": text.strip()[:200],
                                    "expected": "no sanitizer errors",
                                    "got": f["message"], "note": f"{f['kind']}{where}",
                                    "why": WHY.get(f["kind"], "The sanitizer detected undefined or unsafe behaviour here.")})
        n = len(found)
        kinds = sorted({k for k, _ in found})
        fb = "ASan/UBSan clean" if n == 0 else "; ".join(
            f"{f['kind']} at line {f['line']}" if f["line"] else f["kind"] for f in found.values())
        sugg = sorted({WHY[k] for k in kinds if k in WHY})
        return AnalyzerResult(score=max(0.0, 1.0 - 0.34 * n), feedback=fb, suggestions=sugg,
                              evidence={"tests_run": len(cases), "findings": list(found.values()),
                                        "failing": failing[:5]})
