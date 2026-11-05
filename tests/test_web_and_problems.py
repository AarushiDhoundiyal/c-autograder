"""Tests for the documentation JSON, problem packages, second rules file and Django web layer."""
import io
import json
import os
import subprocess
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "autograder_web.settings")
os.environ["GRADER_SYNC"] = "1"

django = pytest.importorskip("django")
django.setup()

from django.conf import settings  # noqa: E402
from django.core.files.uploadedfile import SimpleUploadedFile  # noqa: E402
from django.test import Client  # noqa: E402

from agent.rules import load_rules  # noqa: E402
from agent.testset import discover_tests  # noqa: E402


# ------------------------------------------------------------ docs + problems
def test_usefulness_limitations_complete():
    d = json.loads((ROOT / "docs/usefulness_limitations.json").read_text())
    assert 3 <= len(d["usefulness"]) <= 4 and 3 <= len(d["limitations"]) <= 4
    for u in d["usefulness"]:
        assert {"use_case", "example", "benefit"} <= set(u)
    for l in d["limitations"]:
        assert {"limitation", "example", "mitigation"} <= set(l) and len(l["example"]) > 60


PROBLEMS = ["add", "sum_array", "climb_stairs", "knapsack", "lis", "hanoi", "nqueens",
            "permutations", "reverse_list", "balanced_brackets", "count_occurrences", "longest_run",
            "linked_list_reverse", "graph_components", "stairs_dp"]


@pytest.mark.parametrize("prob", PROBLEMS)
def test_rules_validate_and_weights_sum(prob):
    r = load_rules(ROOT / f"rules/{prob}_full.json")
    names = {m.name for m in r.metrics}
    assert abs(sum(m.weight for m in r.metrics) - 1.0) < 1e-9
    assert len(r.metrics) == (9 if "complexity" in names else 8)


@pytest.mark.parametrize("prob", PROBLEMS)
def test_problem_package_is_complete(prob):
    folder = ROOT / "problems" / prob
    assert (folder / "spec.md").exists() and (folder / "reference.c").exists()
    assert (folder / "edge_cases.json").exists() and len(discover_tests(folder / "tests")) >= 8
    assert len(list((ROOT / "samples").glob(f"{prob}_*.c"))) >= 3


@pytest.mark.parametrize("prob", PROBLEMS)
def test_reference_passes_its_own_tests(prob, tmp_path):
    exe = tmp_path / "ref"
    subprocess.run(["gcc", "-O2", "-std=c11", str(ROOT / f"problems/{prob}/reference.c"), "-o", str(exe)], check=True)
    for t in discover_tests(ROOT / f"problems/{prob}/tests"):
        out = subprocess.run([str(exe)], input=t.input, capture_output=True, text=True).stdout
        assert out.split() == t.expected.split(), t.name


def test_second_problem_needs_no_code_change():
    from agent.coordinator import grade_submission
    good = grade_submission(ROOT / "samples/sum_array_good.c", ROOT / "rules/sum_array_full.json")
    bug = grade_submission(ROOT / "samples/sum_array_offbyone.c", ROOT / "rules/sum_array_full.json")
    assert good["grade"] > 90 and bug["grade"] < good["grade"] - 20
    corr = {m["name"]: m for m in bug["metrics"]}["correctness"]
    assert corr["evidence"]["failing"][0]["expected"].strip()


def test_report_contains_limitations_section():
    from agent.coordinator import grade_submission
    from agent.report import render_text
    txt = render_text(grade_submission(ROOT / "samples/add_good.c", ROOT / "rules/add_full.json"))
    assert "Usefulness & limitations" in txt and "Limits of this report" in txt


# ------------------------------------------------------------------ Django
@pytest.fixture(autouse=True)
def _db(tmp_path, monkeypatch):
    from django.core.management import call_command
    monkeypatch.setattr(settings, "MEDIA_ROOT", tmp_path / "media")
    db = tmp_path / "t.sqlite3"
    settings.DATABASES["default"]["NAME"] = str(db)
    from django.db import connections
    connections.close_all()
    call_command("migrate", verbosity=0, run_syncdb=True)
    call_command("seed_demo", verbosity=0)
    yield
    connections.close_all()


def _client(name, pw):
    c = Client()
    assert c.login(username=name, password=pw)
    return c


def _up(name, text):
    return SimpleUploadedFile(name, text.encode() if isinstance(text, str) else text)


def test_login_required():
    r = Client().get("/")
    assert r.status_code == 302 and "/login/" in r["Location"]


def test_upload_grades_and_report_page():
    from grader.models import GradingRun
    c = _client("student1", "student123")
    r = c.post("/problems/add/", {"file": _up("add.c", (ROOT / "samples/add_basic.c").read_text())})
    assert r.status_code == 302
    run = GradingRun.objects.get()
    assert run.status == "done" and run.grade is not None and run.metrics.count() == 9
    page = c.get(f"/runs/{run.id}/").content.decode()
    assert "Where you failed" in page and "2147483647 1" in page
    assert c.get(f"/runs/{run.id}/download/txt/").status_code == 200


def test_upload_validation():
    c = _client("student1", "student123")
    for name, data in [("x.txt", "int main(){}"), ("x.c", b"\x00\x01"), ("x.c", ""),
                       ("x.c", "a" * (settings.MAX_UPLOAD_BYTES + 1))]:
        r = c.post("/problems/add/", {"file": _up(name, data)})
        assert r.status_code == 200          # form re-rendered with an error, nothing graded
    from grader.models import Submission
    assert Submission.objects.count() == 0


def test_student_cannot_see_other_students_run():
    from django.contrib.auth import get_user_model
    from grader.models import GradingRun
    get_user_model().objects.create_user("other", password="pw12345")
    c1 = _client("student1", "student123")
    c1.post("/problems/add/", {"file": _up("a.c", (ROOT / "samples/add_good.c").read_text())})
    run = GradingRun.objects.get()
    assert _client("other", "pw12345").get(f"/runs/{run.id}/").status_code == 404
    assert _client("teacher", "teacher123").get(f"/runs/{run.id}/").status_code == 200


def test_student_blocked_from_instructor_pages():
    c = _client("student1", "student123")
    assert c.get("/instructor/add/").status_code == 302
    assert c.get("/instructor/add/rules/").status_code == 302


def test_infinite_loop_is_partial_report_not_hang():
    from grader.models import GradingRun
    c = _client("student1", "student123")
    c.post("/problems/add/", {"file": _up("l.c", (ROOT / "samples/add_loop.c").read_text())})
    run = GradingRun.objects.get()
    assert run.status == "done" and run.partial and run.flags.filter(kind="suspected_infinite_loop").exists()


def test_rate_limit_active_jobs(monkeypatch):
    from grader import jobs
    from grader.models import GradingRun
    monkeypatch.setattr(jobs, "enqueue", lambda run_id: None)           # leave runs 'queued'
    c = _client("student1", "student123")
    src = (ROOT / "samples/add_good.c").read_text()
    for _ in range(settings.MAX_ACTIVE_JOBS_PER_USER):
        assert c.post("/problems/add/", {"file": _up("a.c", src)}).status_code == 302
    r = c.post("/problems/add/", {"file": _up("a.c", src)})
    assert r.status_code == 200 and b"waiting" in r.content
    assert GradingRun.objects.count() == settings.MAX_ACTIVE_JOBS_PER_USER


def test_rule_editor_validates_and_versions():
    from grader.models import Problem
    t = _client("teacher", "teacher123")
    p = Problem.objects.get(slug="add")
    n = p.rulesets.count()
    bad = json.loads(p.active_ruleset().json_text)
    bad["metrics"][0]["weight"] = 0.5
    bad["metrics"][1]["analyzer"] = "nope"
    r = t.post("/instructor/add/rules/", {"json_text": json.dumps(bad), "note": ""})
    page = r.content.decode()
    assert r.status_code == 200 and "must sum to 1.00" in page and "unknown analyzer" in page
    assert p.rulesets.count() == n
    ok = json.loads(p.active_ruleset().json_text)
    ok["time_limit_s"] = 2
    assert t.post("/instructor/add/rules/", {"json_text": json.dumps(ok), "note": "slower"}).status_code == 302
    assert p.rulesets.count() == n + 1


def test_dashboard_csv_bulk_upload_and_regrade_identical():
    from grader.models import GradingRun
    t = _client("teacher", "teacher123")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("alice.c", (ROOT / "samples/add_good.c").read_text())
        z.writestr("../evil/bob.c", (ROOT / "samples/add_basic.c").read_text())   # path is ignored
    r = t.post("/instructor/add/", {"archive": _up("all.zip", buf.getvalue())})
    assert r.status_code == 302
    csv_text = t.get("/instructor/add/grades.csv").content.decode()
    assert "alice" in csv_text and "bob" in csv_text and csv_text.splitlines()[0].startswith("student,grade")
    run = GradingRun.objects.filter(submission__student__username="alice").first()
    t.post(f"/runs/{run.id}/regrade/")
    a, b = GradingRun.objects.filter(submission__student__username="alice").order_by("id")
    assert a.grade == b.grade and a.report_json == b.report_json     # reproducible


def test_api_submit_and_fetch():
    import base64
    h = {"HTTP_AUTHORIZATION": "Basic " + base64.b64encode(b"student1:student123").decode()}
    c = Client()
    assert c.post("/api/submissions/", {}).status_code == 401
    r = c.post("/api/submissions/", {"problem": "add", "file": _up("a.c", (ROOT / "samples/add_good.c").read_text())}, **h)
    assert r.status_code == 202
    body = c.get(f"/api/runs/{r.json()['run_id']}/", **h).json()
    assert body["status"] == "done" and body["grade"] > 90 and "report" in body
    assert c.post("/api/submissions/", {"problem": "zzz", "file": _up("a.c", "x")}, **h).status_code == 404


def test_copy_flags_hidden_from_students():
    from grader.models import Flag, GradingRun
    c = _client("student1", "student123")
    c.post("/problems/add/", {"file": _up("a.c", (ROOT / "samples/add_good.c").read_text())})
    run = GradingRun.objects.get()
    Flag.objects.create(run=run, kind="similarity", detail="SECRETDETAIL")
    assert b"SECRETDETAIL" not in c.get(f"/runs/{run.id}/").content
    assert b"SECRETDETAIL" in _client("teacher", "teacher123").get(f"/runs/{run.id}/").content


def test_classmates_are_compared_but_not_the_students_own_work():
    from django.contrib.auth.models import User
    from grader.models import GradingRun
    User.objects.create_user("student2", password="pw2")
    code = (ROOT / "samples/add_good.c").read_text()
    s1 = _client("student1", "student123")
    s1.post("/problems/add/", {"file": _up("a.c", code)})
    s1.post("/problems/add/", {"file": _up("a.c", code)})
    first, second = GradingRun.objects.order_by("id")
    assert not second.flags.filter(kind="similarity").exists()
    _client("student2", "pw2").post("/problems/add/", {"file": _up("b.c", code)})
    third = GradingRun.objects.order_by("id").last()
    flag = third.flags.get(kind="similarity")
    assert "peers/student1.c" in flag.detail

