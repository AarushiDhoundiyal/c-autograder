import json
import pytest
from agent import registry
from agent.coordinator import grade_submission
from agent.registry import register, AnalyzerResult
from agent.report import render_text

GOOD = '#include <stdio.h>\nint main(){int a,b;scanf("%d %d",&a,&b);printf("%d\\n",a+b);return 0;}\n'
LOOP = '#include <stdio.h>\nint main(){int a;scanf("%d",&a);while(1){} printf("x");return 0;}\n'
BROKEN = '#include <stdio.h>\nint main(){ printf("x") return 0; }\n'


@pytest.fixture(autouse=True)
def fake_analyzers():
    @register("t_src", needs_execution=False)
    class S:
        def run(self, ctx):
            return AnalyzerResult(score=0.5, feedback="half", suggestions=["be better"])

    @register("t_exec", needs_execution=True)
    class E:
        def run(self, ctx):
            r = ctx.sandbox.run([ctx.binary_path], stdin="7 5\n")
            ok = r.stdout.strip() == "12"
            ev = {} if ok else {"failing": [{"input": "7 5", "expected": "12", "got": r.stdout, "why": "wrong sum"}]}
            return AnalyzerResult(score=1.0 if ok else 0.0, feedback="ok" if ok else "wrong", evidence=ev)

    @register("t_boom", needs_execution=False)
    class B:
        def run(self, ctx):
            raise ValueError("boom " + str(ctx.workdir))
    yield
    for n in ("t_src", "t_exec", "t_boom"):
        registry.unregister(n)


def rules_file(tmp_path, policy="zero"):
    p = tmp_path / "rules.json"
    p.write_text(json.dumps({"problem": "add", "time_limit_s": 1, "memory_limit_mb": 64,
        "skipped_policy": policy, "smoke_input": "7 5\n", "metrics": [
        {"name": "src", "analyzer": "t_src", "weight": 0.4},
        {"name": "run", "analyzer": "t_exec", "weight": 0.4},
        {"name": "boom", "analyzer": "t_boom", "weight": 0.2}]}))
    return p


def sub(tmp_path, code, name="s.c"):
    p = tmp_path / name; p.write_text(code); return p


def test_good_submission(tmp_path):
    rep = grade_submission(sub(tmp_path, GOOD), rules_file(tmp_path))
    by = {m["name"]: m for m in rep["metrics"]}
    assert by["src"]["contribution"] == 20.0 and by["run"]["contribution"] == 40.0
    assert by["boom"]["status"] == "error" and "<work>" in by["boom"]["feedback"]
    assert rep["grade"] == 60.0 and rep["partial"] and rep["first_pass"]["smoke_ok"]


def test_compile_failure_skips_execution_metrics(tmp_path):
    rep = grade_submission(sub(tmp_path, BROKEN), rules_file(tmp_path))
    by = {m["name"]: m for m in rep["metrics"]}
    assert not rep["first_pass"]["compiled"] and rep["first_pass"]["compile_errors"]
    assert by["run"]["status"] == "skipped" and by["src"]["status"] == "ok"
    assert rep["grade"] == 20.0


def test_infinite_loop_is_flagged_and_partial(tmp_path):
    rep = grade_submission(sub(tmp_path, LOOP), rules_file(tmp_path))
    assert rep["first_pass"]["suspected_infinite_loop"]
    assert rep["flags"][0]["kind"] == "suspected_infinite_loop"
    assert {m["name"]: m["status"] for m in rep["metrics"]}["run"] == "skipped"


def test_renormalize_policy(tmp_path):
    rep = grade_submission(sub(tmp_path, BROKEN), rules_file(tmp_path, "renormalize"))
    # src earned 20 of its 40 points; active weight = src + boom (error counts as active) = 0.6
    assert rep["grade"] == round(20.0 / 0.6, 2)


def test_failing_input_appears_in_text_report(tmp_path):
    wrong = GOOD.replace("a+b", "a-b")
    rep = grade_submission(sub(tmp_path, wrong), rules_file(tmp_path))
    txt = render_text(rep)
    assert "Where you failed" in txt and "EXPECTED: 12" in txt and "wrong sum" in txt


def test_reports_are_identical_across_ten_runs(tmp_path):
    s, r = sub(tmp_path, GOOD), rules_file(tmp_path)
    first = json.dumps(grade_submission(s, r), sort_keys=True)
    for _ in range(9):
        assert json.dumps(grade_submission(s, r), sort_keys=True) == first


def test_placeholders_skip_cleanly_with_shipped_rules(tmp_path):
    from pathlib import Path
    rules = Path(__file__).resolve().parent.parent / "rules" / "add_full.json"
    rep = grade_submission(sub(tmp_path, GOOD), rules)
    assert len(rep["metrics"]) == 9  # placeholders skip now; real analyzers replace them later
