import json
import pytest
from agent.rules import load_rules, validate_rules, RulesError, canonical_hash

GOOD = {"problem": "p", "time_limit_s": 1, "memory_limit_mb": 64, "metrics": [
    {"name": "a", "analyzer": "io_tests", "weight": 0.6, "params": {}},
    {"name": "b", "analyzer": "compiler_warnings", "weight": 0.4}]}


def write(tmp_path, data):
    p = tmp_path / "r.json"
    p.write_text(json.dumps(data))
    return p


def test_valid_rules_load(tmp_path):
    r = load_rules(write(tmp_path, GOOD))
    assert r.problem == "p" and len(r.metrics) == 2 and r.hash.startswith("sha256:")


def test_weights_must_sum_to_one():
    bad = json.loads(json.dumps(GOOD)); bad["metrics"][0]["weight"] = 0.9
    assert any("sum to 1.00" in e for e in validate_rules(bad))


def test_unknown_analyzer_and_duplicate_name():
    bad = json.loads(json.dumps(GOOD))
    bad["metrics"][1]["analyzer"] = "nope"
    bad["metrics"][1]["name"] = "a"
    errs = validate_rules(bad)
    assert any("unknown analyzer 'nope'" in e for e in errs)
    assert any("duplicate" in e for e in errs)


def test_all_errors_reported_at_once(tmp_path):
    bad = {"problem": "", "time_limit_s": -1, "memory_limit_mb": "x", "oops": 1, "metrics": []}
    with pytest.raises(RulesError) as ei:
        load_rules(write(tmp_path, bad))
    assert len(ei.value.errors) >= 4


def test_missing_and_malformed_file(tmp_path):
    with pytest.raises(RulesError):
        load_rules(tmp_path / "none.json")
    p = tmp_path / "bad.json"; p.write_text("{not json")
    with pytest.raises(RulesError):
        load_rules(p)


def test_hash_is_stable_and_content_sensitive():
    a = canonical_hash(GOOD)
    reordered = {k: GOOD[k] for k in reversed(list(GOOD))}
    assert a == canonical_hash(reordered)
    changed = json.loads(json.dumps(GOOD)); changed["time_limit_s"] = 2
    assert a != canonical_hash(changed)


def test_shipped_rule_sets_are_valid():
    from pathlib import Path
    for f in Path(__file__).resolve().parent.parent.glob("rules/*.json"):
        load_rules(f)
