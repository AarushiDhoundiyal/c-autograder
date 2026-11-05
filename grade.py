#!/usr/bin/env python3
"""AutoGrader command line:  python grade.py add.c --rules rules/add_full.json"""
import argparse
import sys

from agent.coordinator import grade_submission
from agent.report import render_text, write_reports
from agent.rules import RulesError


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Grade a C submission under an instructor rules file.")
    ap.add_argument("source", help="the student's .c file")
    ap.add_argument("--rules", required=True, help="rules JSON file")
    ap.add_argument("--out-dir", default="reports", help="where to write <name>.json/.txt (default: reports)")
    ap.add_argument("--workdir", help="keep build files in this directory (default: temp dir, deleted)")
    ap.add_argument("--peers", help="folder of other students' submissions to compare with for originality")
    ap.add_argument("--quiet", action="store_true", help="do not print the text report")
    args = ap.parse_args(argv)
    try:
        report = grade_submission(args.source, args.rules, workdir=args.workdir, peers_dir=args.peers)
    except RulesError as e:
        print("Invalid rules file:", file=sys.stderr)
        for err in e.errors:
            print(f"  - {err}", file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f"File not found: {e.filename}", file=sys.stderr)
        return 2
    jp, tp = write_reports(report, args.out_dir)
    if not args.quiet:
        print(render_text(report))
    print(f"Wrote {jp} and {tp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
