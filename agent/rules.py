"""Rules file loader and validator.

The instructor edits a JSON file; no code change is needed to add, remove or
re-weight a metric. All problems are reported at once, the weights must sum to
1.00, and the file gets a canonical SHA-256 so a report can prove which rules
produced a grade.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from agent import registry

TOP_KEYS = {"problem", "description", "time_limit_s", "memory_limit_mb",
            "skipped_policy", "smoke_input", "metrics"}
METRIC_KEYS = {"name", "analyzer", "weight", "params", "description"}
SKIPPED_POLICIES = ("zero", "renormalize")


class RulesError(Exception):
    def __init__(self, errors):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


@dataclass(frozen=True)
class MetricSpec:
    name: str
    analyzer: str
    weight: float
    params: dict = field(default_factory=dict)


@dataclass
class Rules:
    path: Path | None
    raw: dict
    hash: str
    problem: str
    time_limit_s: float
    memory_limit_mb: float
    skipped_policy: str
    smoke_input: str
    metrics: list

    @property
    def base_dir(self) -> Path:
        return self.path.parent if self.path else Path.cwd()


def canonical_hash(data: dict) -> str:
    blob = json.dumps(data, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(blob).hexdigest()


def _is_num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate_rules(data) -> list[str]:
    """Return a list of human-readable problems (empty list = valid)."""
    errs: list[str] = []
    if not isinstance(data, dict):
        return ["rules file must contain a JSON object"]

    for k in sorted(set(data) - TOP_KEYS):
        errs.append(f"unknown top-level key '{k}'")
    if not isinstance(data.get("problem"), str) or not data.get("problem"):
        errs.append("'problem' must be a non-empty string")
    for key in ("time_limit_s", "memory_limit_mb"):
        v = data.get(key)
        if not _is_num(v) or v <= 0:
            errs.append(f"'{key}' must be a positive number")
    if "skipped_policy" in data and data["skipped_policy"] not in SKIPPED_POLICIES:
        errs.append(f"'skipped_policy' must be one of {list(SKIPPED_POLICIES)}")
    if "smoke_input" in data and not isinstance(data["smoke_input"], str):
        errs.append("'smoke_input' must be a string")

    metrics = data.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        errs.append("'metrics' must be a non-empty list")
        return errs

    known = registry.names()
    seen: set[str] = set()
    total = 0.0
    for i, m in enumerate(metrics):
        tag = f"metrics[{i}]"
        if not isinstance(m, dict):
            errs.append(f"{tag} must be an object")
            continue
        name = m.get("name")
        tag = f"metric '{name}'" if isinstance(name, str) and name else tag
        for k in sorted(set(m) - METRIC_KEYS):
            errs.append(f"{tag}: unknown key '{k}'")
        if not isinstance(name, str) or not name:
            errs.append(f"{tag}: 'name' must be a non-empty string")
        elif name in seen:
            errs.append(f"{tag}: duplicate metric name")
        else:
            seen.add(name)
        an = m.get("analyzer")
        if not isinstance(an, str) or an not in known:
            errs.append(f"{tag}: unknown analyzer '{an}' (known: {', '.join(known)})")
        w = m.get("weight")
        if not _is_num(w) or not (0 < w <= 1):
            errs.append(f"{tag}: 'weight' must be a number in (0, 1]")
        else:
            total += w
        if "params" in m and not isinstance(m["params"], dict):
            errs.append(f"{tag}: 'params' must be an object")
    if abs(total - 1.0) > 1e-6:
        errs.append(f"weights sum to {total:.4f}; they must sum to 1.00")
    return errs


def load_rules(path) -> Rules:
    path = Path(path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise RulesError([f"rules file not found: {path}"])
    except json.JSONDecodeError as e:
        raise RulesError([f"rules file is not valid JSON: {e}"])
    errs = validate_rules(raw)
    if errs:
        raise RulesError(errs)
    metrics = [MetricSpec(m["name"], m["analyzer"], float(m["weight"]),
                          dict(m.get("params", {}))) for m in raw["metrics"]]
    return Rules(path=path.resolve(), raw=raw, hash=canonical_hash(raw),
                 problem=raw["problem"], time_limit_s=float(raw["time_limit_s"]),
                 memory_limit_mb=float(raw["memory_limit_mb"]),
                 skipped_policy=raw.get("skipped_policy", "zero"),
                 smoke_input=raw.get("smoke_input", ""), metrics=metrics)
