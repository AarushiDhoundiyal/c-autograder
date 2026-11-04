"""Builds a self-contained 'add' problem for tests (so tests never depend on
the repo's own problems/ folder) and a rules file around it."""
import json
from pathlib import Path

SAMPLES = Path(__file__).resolve().parent.parent / "samples"

CASES = [("7 5", 12), ("0 0", 0), ("-3 -4", -7), ("-10 10", 0), ("100 200", 300),
         ("1000000 2000000", 3000000), ("-2147483648 0", -2147483648),
         ("2147483647 0", 2147483647), ("2147483647 1", 2147483648),
         ("-2147483648 -1", -2147483649)]


def make_add_tests(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    for i, (inp, out) in enumerate(CASES, 1):
        (directory / f"{i:03d}.in").write_text(inp + "\n")
        (directory / f"{i:03d}.out").write_text(f"{out}\n")
    return directory


def make_rules(tmp_path: Path, metrics=None) -> Path:
    tests = make_add_tests(tmp_path / "tests")
    default = [
        {"name": "correctness", "analyzer": "io_tests", "weight": 0.35,
         "params": {"testset_dir": str(tests)}},
        {"name": "syntax", "analyzer": "compiler_warnings", "weight": 0.15,
         "params": {"flags": "-Wall -Wextra -std=c11"}},
        {"name": "structure", "analyzer": "static_analysis", "weight": 0.15,
         "params": {"max_cyclomatic": 8, "max_function_length": 40}},
        {"name": "modularity", "analyzer": "function_split", "weight": 0.15,
         "params": {"expect_helpers": True, "min_functions": 2}},
        {"name": "memory_safety", "analyzer": "sanitizer_run", "weight": 0.20,
         "params": {"testset_dir": str(tests)}}]
    p = tmp_path / "rules.json"
    p.write_text(json.dumps({"problem": "add", "time_limit_s": 1, "memory_limit_mb": 64,
                             "smoke_input": "7 5\n", "metrics": metrics or default}))
    return p
