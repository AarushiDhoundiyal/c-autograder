#!/usr/bin/env python3
"""Grade the sample submissions and write one report per sample plus a summary.
    python scripts/run_samples.py [--out-dir reports/final] [problem ...]"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.coordinator import grade_submission  # noqa: E402
from agent.report import write_reports  # noqa: E402

PROBLEMS = ["add", "sum_array", "climb_stairs", "knapsack", "lis", "hanoi", "nqueens",
            "permutations", "reverse_list", "balanced_brackets", "count_occurrences", "longest_run",
            "linked_list_reverse", "graph_components", "stairs_dp"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="reports/final")
    ap.add_argument("problems", nargs="*", help="problem names to grade (default: all)")
    args = ap.parse_args()
    for name in args.problems:
        if name not in PROBLEMS:
            ap.error(f"unknown problem '{name}'; choose from {', '.join(PROBLEMS)}")
    chosen = args.problems or PROBLEMS
    rows = []
    for name in chosen:
        rules = f"rules/{name}_full.json"
        for src in sorted(ROOT.glob(f"samples/{name}_*.c")):
            rep = grade_submission(src, ROOT / rules)
            write_reports(rep, ROOT / args.out_dir)
            rows.append((src.name, Path(rules).stem, rep["grade"], "PARTIAL" if rep["partial"] else "full",
                         ",".join(f["kind"] for f in rep["flags"]) or "-"))
    wide = max([len(r[0]) for r in rows] + [10]) + 2
    lines = [f"{'submission':{wide}}{'rules':26}{'grade':>8}  {'report':8}flags"]
    lines += [f"{a:{wide}}{b:26}{c:8.2f}  {d:8}{e}" for a, b, c, d, e in rows]
    summary = "SUMMARY.txt" if not args.problems else "SUMMARY_" + "-".join(args.problems) + ".txt"
    out = ROOT / args.out_dir / summary
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nreports written to {args.out_dir}/")


if __name__ == "__main__":
    main()
