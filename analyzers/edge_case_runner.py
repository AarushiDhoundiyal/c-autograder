"""logical: differential testing of the submission against the trusted reference.

params:
  reference         path of the reference solution (.c); if missing, a sibling
                    reference*.c in the same folder is used
  edge_cases_file   JSON with named groups of inputs (+ optional "random" section)
  cases             group names to grade (default: every group in the file)
  random_count      override the number of seeded random cases
  compare           "tokens" (default) | "lines" | "exact"
  minimise          true (default): shrink the first failures to minimal inputs
  minimise_drop_tokens  false (default): also try deleting tokens while shrinking
  max_shown         failures listed in the report (default 5)

score = edge cases handled / edge cases. Every failure is a counter-test with
the expected output taken from the reference, never from an LLM.
"""
from pathlib import Path

from agent import counter_tests as ct
from agent.registry import register, AnalyzerResult

TIPS = {
    "overflow": "Use a wider integer type (long long, %lld) or check for overflow before the operation.",
    "crash": "Initialise pointers and check array bounds before using them.",
    "timeout": "Look for a loop that never ends or an algorithm that is too slow.",
}
GROUP_TIPS = {
    "whitespace": "Make input parsing tolerant of extra spaces, tabs and blank lines.",
    "crlf": "Windows line endings (\\r\\n) can appear in input; do not depend on exact line endings.",
    "no_trailing_newline": "The last line of input may have no newline; do not rely on it.",
}


def _find_reference(ctx) -> Path:
    p = ctx.resolve(ctx.params["reference"])
    if p.exists():
        return p
    hits = sorted(p.parent.glob("reference*.c")) if p.parent.is_dir() else []
    if hits:
        return hits[0]
    raise FileNotFoundError(f"reference solution not found: {ctx.params['reference']}")


@register("edge_case_runner", needs_execution=True)
class EdgeCaseRunner:
    def run(self, ctx):
        p = ctx.params
        ref_src = _find_reference(ctx)
        spec = ct.load_edge_cases(ctx.resolve(p["edge_cases_file"]))
        groups = list(p.get("cases") or ct.default_groups(spec))
        ref_bin = ct.build_reference(ctx.sandbox, ref_src, ctx.workdir)
        seed = ct.derive_seed(ctx.rules.hash, ctx.rules.problem)
        results, failing = ct.generate_counter_tests(
            ctx.sandbox, ctx.binary_path, ref_bin, spec, groups, seed,
            compare=p.get("compare", "tokens"), random_count=p.get("random_count"),
            minimise_first=3 if p.get("minimise", True) else 0,
            drop_tokens=bool(p.get("minimise_drop_tokens", False)))
        valid = [r for r in results if r.valid]
        if not valid:
            raise RuntimeError("the reference solution could not answer any edge case")
        passed = sum(1 for r in valid if r.ok)
        per_group = {}
        for r in valid:
            g = per_group.setdefault(r.group, {"passed": 0, "total": 0})
            g["total"] += 1
            g["passed"] += int(r.ok)
        shown = [{k: v for k, v in f.items() if k != "_raw"} for f in failing[:int(p.get("max_shown", 5))]]
        failed_groups = [g for g in groups if g in per_group and per_group[g]["passed"] < per_group[g]["total"]]
        fb = f"{passed}/{len(valid)} edge cases handled"
        if failed_groups:
            fb += "; fails: " + ", ".join(f"{g} ({per_group[g]['total'] - per_group[g]['passed']})"
                                           for g in failed_groups)
        sugg = []
        for k in ("overflow", "crash", "timeout"):
            if any(f["kind"] == k for f in failing):
                sugg.append(TIPS[k])
        sugg += [GROUP_TIPS[g] for g in failed_groups if g in GROUP_TIPS]
        if failing and not sugg:
            sugg.append("Compare your output with the expected output on the counter-test inputs above.")
        ev = {"cases_passed": passed, "cases_total": len(valid), "groups": per_group,
              "invalid_cases": len(results) - len(valid), "counter_tests_found": len(failing),
              "failing": shown}
        if "random" in groups:
            ev["random_seed"] = seed
        return AnalyzerResult(score=passed / len(valid), evidence=ev, feedback=fb, suggestions=sugg)
