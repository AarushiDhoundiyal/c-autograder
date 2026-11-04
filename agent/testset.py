"""Loads a problem's test directory: every NNN.in with a matching NNN.out
(or .ans / .expected). Sorted by name, so order is reproducible."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCase:
    __test__ = False          # not a pytest class
    name: str
    input: str
    expected: str | None


def discover_tests(path) -> list:
    root = Path(path)
    if not root.is_dir():
        raise FileNotFoundError(f"test directory not found: {path}")
    cases = []
    for inp in sorted(root.rglob("*.in")):
        expected = None
        for ext in (".out", ".ans", ".expected"):
            cand = inp.with_suffix(ext)
            if cand.exists():
                expected = cand.read_text(encoding="utf-8", errors="replace")
                break
        cases.append(TestCase(inp.relative_to(root).with_suffix("").as_posix(),
                              inp.read_text(encoding="utf-8", errors="replace"), expected))
    if not cases:
        raise ValueError(f"no *.in test files found in {path}")
    return cases
