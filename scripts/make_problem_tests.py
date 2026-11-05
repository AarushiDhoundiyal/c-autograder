#!/usr/bin/env python3
"""Write the hidden test sets problems/<name>/tests/NNN.in/.out.
Expected outputs are computed here in Python, independently of the C reference solutions and
never by a student program. The five problems of the five-assignment test pack keep their reviewed
cases in problems/<name>/teacher_cases.json, and their tests are written from that file.
Existing files are never overwritten unless --force is given:
    python scripts/make_problem_tests.py"""
import argparse
import bisect
import itertools
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADD = ["7 5", "0 0", "-3 -4", "-10 10", "100 200", "1000000 2000000",
       "-2147483648 0", "2147483647 0", "2147483647 1", "-2147483648 -1"]
MOD = 1_000_000_007


def add_cases():
    return [x + "\n" for x in ADD], [str(sum(int(t) for t in x.split())) for x in ADD]


def sum_array_cases():
    rng = random.Random(2026)
    cases = [[], [5], [-5], [1, 2, 3], [-1, -2, -3], [2147483647, 1], [-2147483648, -1],
             [2147483647] * 3, [0, 0, 0, 0, 7]]
    cases.append([rng.randint(-1000, 1000) for _ in range(50)])
    cases.append([rng.randint(0, 1000) for _ in range(5000)])
    return [f"{len(c)}\n" + " ".join(map(str, c)) + "\n" for c in cases], [str(sum(c)) for c in cases]


def climb_stairs(n):
    a, b = 1, 1
    for _ in range(2, n + 1):
        a, b = b, (a + b) % MOD
    return str(b)


def climb_stairs_cases():
    ns = [0, 1, 2, 3, 10, 44, 45, 46, 100, 1000, 100000, 1000000]
    return [f"{n}\n" for n in ns], [climb_stairs(n) for n in ns]


def knapsack(cap, items):
    best = [0] * (cap + 1)
    for w, v in items:
        for c in range(cap, w - 1, -1):
            best[c] = max(best[c], best[c - w] + v)
    return str(best[cap])


def knapsack_cases():
    rng = random.Random(2027)
    cases = [(50, [(10, 60), (20, 100), (30, 120)]), (100, []), (0, [(1, 5), (2, 6), (3, 7)]),
             (5, [(6, 100), (7, 200)]), (10, [(10, 42)]),
             (10, [(5, 10), (4, 40), (6, 30), (3, 50)]), (10, [(6, 30), (5, 20), (5, 20)])]
    for n, cap, wmax in ((20, 1000, 300), (50, 5000, 1000), (100, 10000, 2000)):
        cases.append((cap, [(rng.randint(1, wmax), rng.randint(0, 1_000_000)) for _ in range(n)]))
    ins = [f"{len(items)} {cap}\n" + "".join(f"{w} {v}\n" for w, v in items) for cap, items in cases]
    return ins, [knapsack(cap, items) for cap, items in cases]


def lis(values):
    tails = []
    for x in values:
        i = bisect.bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return str(len(tails))


def lis_cases():
    rng = random.Random(2028)
    cases = [[10, 9, 2, 5, 3, 7, 101, 18], [], [42], [7] * 5, [6, 5, 4, 3, 2, 1], list(range(1, 11)),
             [1, 3, 3, 5, 5, 7, 2, 8], [-2147483648, 2147483647, -2147483648, 2147483647],
             [rng.randint(-10**6, 10**6) for _ in range(1000)],
             [rng.randint(-2**31, 2**31 - 1) for _ in range(5000)]]
    return [f"{len(c)}\n" + " ".join(map(str, c)) + "\n" for c in cases], [lis(c) for c in cases]


def hanoi(n):
    moves = []

    def go(k, src, dst, via):
        if k:
            go(k - 1, src, via, dst)
            moves.append(f"Move disk {k} from {src} to {dst}")
            go(k - 1, via, dst, src)

    go(n, "A", "C", "B")
    return "\n".join(moves + [f"Total moves: {len(moves)}"])


def hanoi_cases():
    ns = [0, 1, 2, 3, 4, 5, 7, 8, 10, 12]
    return [f"{n}\n" for n in ns], [hanoi(n) for n in ns]


def nqueens(n):
    full = (1 << n) - 1

    def count(cols, left, right):
        if cols == full:
            return 1
        total, free = 0, full & ~(cols | left | right)
        while free:
            bit = free & -free
            free ^= bit
            total += count(cols | bit, ((left | bit) << 1) & full, (right | bit) >> 1)
        return total

    return str(count(0, 0, 0))


def nqueens_cases():
    ns = list(range(1, 11))
    return [f"{n}\n" for n in ns], [nqueens(n) for n in ns]


def permutations_cases():
    ns = list(range(1, 9))
    outs = ["\n".join(" ".join(map(str, p)) for p in itertools.permutations(range(1, n + 1))) for n in ns]
    return [f"{n}\n" for n in ns], outs


def reverse_list_cases():
    rng = random.Random(2029)
    cases = [[], [7], [1, 2], [1, 2, 3, 4, 5], [-3, 0, 3, -2147483648, 2147483647], [4, 4, 1, 4, 1],
             [rng.randint(-10**6, 10**6) for _ in range(1000)],
             [rng.randint(-1000, 1000) for _ in range(100000)]]
    ins = [f"{len(c)}\n" + " ".join(map(str, c)) + "\n" for c in cases]
    ins.append("6\n1 2\n3\n\n4   5\t6\n")
    outs = [" ".join(map(str, reversed(c))) for c in cases] + ["6 5 4 3 2 1"]
    return ins, outs


def balanced(text):
    pairs, stack = {")": "(", "]": "[", "}": "{"}, []
    for ch in text:
        if ch in "([{":
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return "NO"
    return "YES" if not stack else "NO"


def random_balanced(rng, pairs):
    out, stack = [], []
    while pairs or stack:
        if pairs and (not stack or rng.random() < 0.55):
            ch = rng.choice("([{")
            out.append(ch)
            stack.append(ch)
            pairs -= 1
        else:
            out.append({"(": ")", "[": "]", "{": "}"}[stack.pop()])
        if rng.random() < 0.1:
            out.append(rng.choice("ab x+1;"))
    return "".join(out)


def balanced_brackets_cases():
    rng = random.Random(2030)
    deep = "(" * 49999 + ")" * 49999
    ok_long = random_balanced(rng, 5000)
    cases = ["{[()()]}\n", "([)]\n", "((\n", "))\n", "", "a(b)c[d]{e} = 1;\n", "}{\n",
             deep + "\n", deep + "]\n", ok_long + "\n", ok_long.rstrip("ab x+1;")[:-1] + "\n"]
    return cases, [balanced(c) for c in cases]


def teacher_pack(name):
    def cases():
        data = json.loads((ROOT / "problems" / name / "teacher_cases.json").read_text(encoding="utf-8"))
        return [c["stdin"] for c in data], [c["expected_output"].rstrip("\n") for c in data]
    return cases


PROBLEMS = {
    "add": add_cases,
    "sum_array": sum_array_cases,
    "climb_stairs": climb_stairs_cases,
    "knapsack": knapsack_cases,
    "lis": lis_cases,
    "hanoi": hanoi_cases,
    "nqueens": nqueens_cases,
    "permutations": permutations_cases,
    "reverse_list": reverse_list_cases,
    "balanced_brackets": balanced_brackets_cases,
    "count_occurrences": teacher_pack("count_occurrences"),
    "longest_run": teacher_pack("longest_run"),
    "linked_list_reverse": teacher_pack("linked_list_reverse"),
    "graph_components": teacher_pack("graph_components"),
    "stairs_dp": teacher_pack("stairs_dp"),
}


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
    ap.add_argument("problems", nargs="*", help="problem names (default: all)")
    args = ap.parse_args()
    for name in args.problems or PROBLEMS:
        if name not in PROBLEMS:
            ap.error(f"unknown problem '{name}'; choose from {', '.join(PROBLEMS)}")
        ins, outs = PROBLEMS[name]()
        write(ROOT / "problems" / name / "tests", ins, outs, args.force)


if __name__ == "__main__":
    main()
