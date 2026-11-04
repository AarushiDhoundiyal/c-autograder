#!/usr/bin/env python3
"""Write the hidden test sets problems/<name>/tests/NNN.in/.out.
Expected outputs are computed here with Python big integers (exact maths), NOT by a student program.
Existing files are never overwritten unless --force is given:   python scripts/make_problem_tests.py"""
import argparse
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADD = ["7 5", "0 0", "-3 -4", "-10 10", "100 200", "1000000 2000000",
       "-2147483648 0", "2147483647 0", "2147483647 1", "-2147483648 -1"]


def sum_array_cases():
    rng = random.Random(2026)
    cases = [[], [5], [-5], [1, 2, 3], [-1, -2, -3], [2147483647, 1], [-2147483648, -1],
             [2147483647] * 3, [0, 0, 0, 0, 7]]
    cases.append([rng.randint(-1000, 1000) for _ in range(50)])
    cases.append([rng.randint(0, 1000) for _ in range(5000)])
    return [f"{len(c)}\n" + " ".join(map(str, c)) + "\n" for c in cases], [str(sum(c)) for c in cases]


def write(folder: Path, ins, outs, force):
    folder.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, (a, b) in enumerate(zip(ins, outs), 1):
        fi, fo = folder / f"{i:03d}.in", folder / f"{i:03d}.out"
        if force or not (fi.exists() and fo.exists()):
            fi.write_text(a)
            fo.write_text(b + "\n")
            n += 1
    print(f"{folder.relative_to(ROOT)}: {len(ins)} tests ({n} written)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    ins = [x + "\n" for x in ADD]
    outs = [str(sum(int(t) for t in x.split())) for x in ADD]
    write(ROOT / "problems/add/tests", ins, outs, args.force)
    ins, outs = sum_array_cases()
    write(ROOT / "problems/sum_array/tests", ins, outs, args.force)


if __name__ == "__main__":
    main()
