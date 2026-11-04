"""Analyzer registry and the shared analyzer interface.

Every metric is graded by one analyzer class. An analyzer is registered under
the name the rules file uses in its "analyzer" field:

    from agent.registry import register, AnalyzerResult, AnalyzerContext

    @register("io_tests", needs_execution=True)
    class IoTests:
        def run(self, ctx: AnalyzerContext) -> AnalyzerResult:
            ...

Registering a name twice replaces the earlier entry. This is how the real
analyzers replace the placeholders from analyzers/pending.py.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalyzerResult:
    score: float = 0.0                              # 0.0 .. 1.0
    evidence: dict = field(default_factory=dict)    # JSON-serialisable raw facts
    feedback: str = ""                              # one short line for the table
    suggestions: list = field(default_factory=list)  # advice for the student
    flags: list = field(default_factory=list)       # [{"kind":..., "detail":...}]
    status: str = "ok"                              # ok | skipped | error


@dataclass
class AnalyzerContext:
    source_path: Path
    binary_path: Path | None      # compiled with the first-pass flags (None if compile failed)
    workdir: Path                 # private scratch directory, deleted after grading
    params: dict                  # this metric's "params" slice from the rules file
    rules: Any                    # agent.rules.Rules
    sandbox: Any                  # agent.sandbox.Sandbox
    first_pass: dict              # results of compile check / smoke run / static sanity
    base_dirs: list = field(default_factory=list)

    @property
    def time_limit_s(self) -> float:
        return self.rules.time_limit_s

    @property
    def memory_limit_mb(self) -> float:
        return self.rules.memory_limit_mb

    def resolve(self, p) -> Path:
        """Resolve a path from the rules file: absolute, else first existing
        match under the current directory, the rules file directory, repo root."""
        p = Path(p)
        if p.is_absolute():
            return p
        for base in self.base_dirs:
            cand = Path(base) / p
            if cand.exists():
                return cand
        return Path(self.base_dirs[0]) / p if self.base_dirs else p


@dataclass
class _Entry:
    name: str
    cls: type
    needs_execution: bool


_REGISTRY: dict[str, _Entry] = {}


def register(name: str, needs_execution: bool = False):
    def deco(cls):
        _REGISTRY[name] = _Entry(name, cls, needs_execution)
        return cls
    return deco


def unregister(name: str) -> None:
    _REGISTRY.pop(name, None)


def _ensure_loaded() -> None:
    import analyzers  # noqa: F401  (importing the package registers everything)


def get(name: str) -> _Entry:
    _ensure_loaded()
    return _REGISTRY[name]


def names() -> list[str]:
    _ensure_loaded()
    return sorted(_REGISTRY)
