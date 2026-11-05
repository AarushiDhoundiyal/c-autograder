"""correctness: run the binary on every NNN.in and compare with NNN.out.

params: testset_dir (required), compare = "tokens" (default) | "lines" | "exact"
score = passed / total. Failures are classified (wrong output, timeout, crash,
non-zero exit, output flood) and explained from a template.
"""
from agent import sandbox as sbx
from agent.registry import register, AnalyzerResult
from agent.testset import discover_tests

INT_MAX, INT_MIN = 2**31 - 1, -2**31
MAX_FAILURES_SHOWN = 5


def clip(text: str, n: int = 200) -> str:
    text = str(text)
    return text if len(text) <= n else text[:n] + "...[cut]"


def same(expected: str, got: str, mode: str) -> bool:
    if mode == "exact":
        return expected == got
    if mode == "lines":
        norm = lambda t: [l.rstrip() for l in t.rstrip("\n").splitlines()]
        return norm(expected) == norm(got)
    return expected.split() == got.split()


def _wrap32(v: int) -> int:
    return (v + 2**31) % 2**32 - 2**31


def explain(expected: str, got: str, run, limit_s: float):
    """Return (kind, note, why) for a failed test."""
    if run.outcome == sbx.TIMEOUT:
        return ("timeout", f"timed out after {limit_s:g}s",
                "The program did not finish in time. Look for a loop that never ends "
                "or an algorithm that is too slow for this input.")
    if run.outcome == sbx.OUTPUT_LIMIT:
        return ("output_flood", "output limit exceeded",
                "The program printed far more than expected, usually an endless output loop.")
    if run.outcome == sbx.SIGNAL:
        sig = run.signal
        why = {"SIGSEGV": "Invalid memory access, for example a null or uninitialised pointer, "
                          "or an index outside an array.",
               "SIGFPE": "Arithmetic fault, typically division by zero.",
               "SIGABRT": "The program aborted: failed assertion, double free or heap corruption."
               }.get(sig, f"The program was killed by signal {sig}.")
        return ("crash", f"crashed with {sig}", why)
    if run.outcome == sbx.RUNTIME_ERROR:
        return ("nonzero_exit", f"exit status {run.returncode}",
                f"The program exited with status {run.returncode}. main() must return 0 when it succeeds.")
    toks = expected.split()
    if len(toks) == 1:
        try:
            e = int(toks[0])
        except ValueError:
            e = None
        if e is not None and not (INT_MIN <= e <= INT_MAX):
            return ("overflow", "integer overflow",
                    f"The correct answer {e} does not fit in a 32-bit int, so the arithmetic "
                    "overflowed. Use 'long long' (and %lld) or check the range before adding.")
    if not got.strip():
        return ("no_output", "no output",
                "The program printed nothing. Check that the input is read correctly and the "
                "answer is printed with printf.")
    return ("wrong_output", "wrong output",
            "The output differs from the expected output. Look for a wrong formula, an off-by-one "
            "error or a formatting difference (extra text, missing newline).")


@register("io_tests", needs_execution=True)
class IoTests:
    def run(self, ctx):
        mode = ctx.params.get("compare", "tokens")
        tests = discover_tests(ctx.resolve(ctx.params["testset_dir"]))
        missing = [t.name for t in tests if t.expected is None]
        if missing:
            raise ValueError(f"no expected-output file for test(s): {', '.join(missing[:3])}")
        passed, failing, kinds = 0, [], []
        for t in tests:
            run = ctx.sandbox.run([ctx.binary_path], stdin=t.input)
            if run.ok and same(t.expected, run.stdout, mode):
                passed += 1
                continue
            kind, note, why = explain(t.expected, run.stdout, run, ctx.time_limit_s)
            kinds.append(kind)
            failing.append({"test": t.name, "input": clip(t.input.strip()),
                            "expected": clip(t.expected.strip()), "got": clip(run.stdout.strip()),
                            "note": note, "why": why, "kind": kind})
        total = len(tests)
        fb = f"{passed}/{total} tests pass"
        if failing:
            fb += f"; first failure: test {failing[0]['test']} ({failing[0]['note']})"
        sugg = []
        if failing:
            sugg.append("Run the failing input by hand and compare your output with the expected output.")
        if "overflow" in kinds:
            sugg.append("Use a wider integer type (long long) or check for overflow before the operation.")
        if "crash" in kinds:
            sugg.append("Initialise pointers and check array bounds before using them.")
        return AnalyzerResult(score=passed / total if total else 0.0,
                              evidence={"tests_passed": passed, "tests_total": total,
                                        "failing_tests": [f["test"] for f in failing],
                                        "failing": failing[:MAX_FAILURES_SHOWN]},
                              feedback=fb, suggestions=sugg)
