#!/usr/bin/env python3
"""Grade every sample submission and write reports + a summary (the 'agent output on the samples'
deliverable).   python scripts/run_samples.py [--out-dir reports/final]"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.coordinator import grade_submission  # noqa: E402
from agent.report import write_reports  # noqa: E402

PLAN = [("samples/add_*.c", "rules/add_full.json"),
        ("samples/sum_array_*.c", "rules/sum_array_full.json")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="reports/final")
    args = ap.parse_args()
    rows = []
    for pattern, rules in PLAN:
        for src in sorted(ROOT.glob(pattern)):
            rep = grade_submission(src, ROOT / rules)
            write_reports(rep, ROOT / args.out_dir)
            rows.append((src.name, Path(rules).stem, rep["grade"], "PARTIAL" if rep["partial"] else "full",
                         ",".join(f["kind"] for f in rep["flags"]) or "-"))
    lines = [f"{'submission':26}{'rules':18}{'grade':>8}  {'report':8}flags"]
    lines += [f"{a:26}{b:18}{c:8.2f}  {d:8}{e}" for a, b, c, d, e in rows]
    out = ROOT / args.out_dir / "SUMMARY.txt"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nreports written to {args.out_dir}/")


if __name__ == "__main__":
    main()
