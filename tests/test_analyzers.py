import json
import pytest
from agent.coordinator import grade_submission
from agent.report import render_text
from analyzers.sanitizer_run import parse_sanitizer
from tests.helpers import SAMPLES, make_rules

_cache = {}


@pytest.fixture(scope="module")
def grades(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("rules")
    rules = make_rules(tmp)
    return lambda name: _cache.setdefault(name, grade_submission(SAMPLES / name, rules))


def metric(rep, name):
    return next(m for m in rep["metrics"] if m["name"] == name)


def test_good_submission_scores_full(grades):
    rep = grades("add_good.c")
    assert rep["grade"] == 100.0 and not rep["partial"]
    assert metric(rep, "correctness")["evidence"]["tests_passed"] == 10


def test_basic_submission_overflow_is_explained(grades):
    rep = grades("add_basic.c")
    c = metric(rep, "correctness")
    assert c["evidence"]["tests_passed"] == 8                 # two inputs overflow int
    f = c["evidence"]["failing"][0]
    assert f["input"] == "2147483647 1" and f["expected"] == "2147483648"
    assert "32-bit" in f["why"] and f["kind"] == "overflow"
    assert metric(rep, "modularity")["score"] == 0.3          # only main()
    assert metric(rep, "syntax")["evidence"]["warnings"] >= 1  # unused scanf result
    mem = metric(rep, "memory_safety")
    assert any(x["kind"] == "signed-integer-overflow" for x in mem["evidence"]["findings"])
    assert mem["evidence"]["failing"][0]["input"] in ("2147483647 1", "-2147483648 -1")


def test_leak_is_found_with_line_number(grades):
    rep = grades("add_leak.c")
    f = metric(rep, "memory_safety")["evidence"]["findings"]
    assert [x["kind"] for x in f] == ["memory-leak"] and f[0]["line"] == 8
    assert metric(rep, "correctness")["score"] == 1.0


def test_crash_is_classified(grades):
    rep = grades("add_crash.c")
    c = metric(rep, "correctness")
    assert c["score"] == 0.0 and c["evidence"]["failing"][0]["kind"] == "crash"
    assert "SIGSEGV" in c["evidence"]["failing"][0]["note"]


def test_infinite_loop_gives_partial_report(grades):
    rep = grades("add_loop.c")
    assert rep["first_pass"]["suspected_infinite_loop"] and rep["partial"]
    st = {m["name"]: m["status"] for m in rep["metrics"]}
    assert st["correctness"] == "skipped" and st["memory_safety"] == "skipped"
    assert st["syntax"] == "ok" and st["modularity"] == "ok"


def test_broken_submission_still_gets_source_metrics(grades):
    rep = grades("add_broken.c")
    st = {m["name"]: m["status"] for m in rep["metrics"]}
    assert not rep["first_pass"]["compiled"]
    assert st["correctness"] == "skipped" and st["structure"] == "ok"
    assert metric(rep, "syntax")["score"] == 0.0
    assert "Does not compile" in metric(rep, "syntax")["feedback"]


def test_grade_ordering_matches_quality(grades):
    g = {n: grades(n)["grade"] for n in ("add_good.c", "add_leak.c", "add_basic.c",
                                         "add_crash.c", "add_loop.c", "add_broken.c")}
    assert g["add_good.c"] > g["add_leak.c"] > g["add_basic.c"] > g["add_crash.c"]
    assert g["add_loop.c"] < g["add_basic.c"] and g["add_broken.c"] < g["add_basic.c"]


def test_text_report_shows_failing_input_beside_expected(grades):
    txt = render_text(grades("add_basic.c"))
    assert "INPUT:    2147483647 1" in txt and "EXPECTED: 2147483648" in txt


def test_werror_in_rules_is_counted_not_fatal(tmp_path):
    from tests.helpers import make_rules
    m = [{"name": "syntax", "analyzer": "compiler_warnings", "weight": 1.0,
          "params": {"flags": "-Wall -Wextra -Werror -std=c11"}}]
    rep = grade_submission(SAMPLES / "add_basic.c", make_rules(tmp_path, m))
    ev = metric(rep, "syntax")["evidence"]
    assert ev["werror_removed"] and ev["compiled"] and 0 < metric(rep, "syntax")["score"] < 1


def test_missing_testset_isolated_as_error(tmp_path):
    m = [{"name": "correctness", "analyzer": "io_tests", "weight": 1.0,
          "params": {"testset_dir": str(tmp_path / "nope")}}]
    rep = grade_submission(SAMPLES / "add_good.c", make_rules(tmp_path, m))
    assert metric(rep, "correctness")["status"] == "error" and rep["grade"] == 0.0


def test_ten_run_determinism_with_real_analyzers(tmp_path):
    rules = make_rules(tmp_path)
    first = json.dumps(grade_submission(SAMPLES / "add_basic.c", rules), sort_keys=True)
    for _ in range(9):
        assert json.dumps(grade_submission(SAMPLES / "add_basic.c", rules), sort_keys=True) == first


def test_parse_sanitizer_variants():
    ub = "add.c:5:19: runtime error: signed integer overflow: 2147483647 + 1 cannot be represented in type 'int'"
    assert parse_sanitizer(ub, "add.c")[0]["kind"] == "signed-integer-overflow"
    leak = "==1==ERROR: LeakSanitizer: detected memory leaks\nDirect leak of 8 byte(s) in 1 object(s) allocated from:\n    #0 0x1 in malloc\n    #1 0x2 in main add.c:4\n"
    f = parse_sanitizer(leak, "add.c")
    assert f == [{"kind": "memory-leak", "line": 4, "message": "8 byte(s) leaked"}]
    assert parse_sanitizer(ub + "\n" + ub, "add.c").__len__() == 1       # deduplicated


def test_parse_sanitizer_output_does_not_depend_on_memory_layout():
    a = "p.c:15:9: runtime error: load of address 0x561a2cce7edc with insufficient space for an object of type 'int'"
    b = a.replace("0x561a2cce7edc", "0x5586df554edc")
    assert parse_sanitizer(a, "p.c") == parse_sanitizer(b, "p.c")
    assert "<address>" in parse_sanitizer(a, "p.c")[0]["message"]
    so = "==1==ERROR: AddressSanitizer: stack-overflow on address 0x7ffd\n    #0 0x5 in ways p.c:{}"
    first, second = parse_sanitizer(so.format(6), "p.c"), parse_sanitizer(so.format(10), "p.c")
    assert first == second and first[0]["kind"] == "stack-overflow" and first[0]["line"] is None
