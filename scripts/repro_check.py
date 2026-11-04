#!/usr/bin/env python3
"""Reproducibility campaign: grade each submission N times and require byte-identical JSON reports
(same submission + same rules = same grade).
    python scripts/repro_check.py --runs 10 [samples/add_basic.c ...] [--rules rules/add_full.json]
Exit code 0 only if every submission produced identical reports on every run."""
import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from agent.coordinator import grade_submission  # noqa: E402
from agent.report import report_to_json  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--rules", default="rules/add_full.json")
    ap.add_argument("--runs", type=int, default=10)
    args = ap.parse_args()
    files = [Path(f) for f in args.files] or sorted((ROOT / "samples").glob("add_*.c"))
    bad = 0
    for f in files:
        digests, grade = set(), None
        for _ in range(args.runs):
            rep = grade_submission(f, ROOT / args.rules if not Path(args.rules).exists() else args.rules)
            digests.add(hashlib.sha256(report_to_json(rep).encode()).hexdigest())
            grade = rep["grade"]
        ok = len(digests) == 1
        bad += not ok
        print(f"{'OK  ' if ok else 'FAIL'} {f.name:24} grade {grade:7.2f}  {args.runs} runs, {len(digests)} distinct report(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
