"""Background job runner. A view only stores the upload and enqueues a run; this worker grades it by
launching `python grade.py` (or `docker run ... --network none`) as a CHILD PROCESS, so student code
never executes inside the Django process. One daemon worker thread runs the jobs; pages poll the run status."""
import json
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

from agent import REPO_ROOT

_q: "queue.Queue[int]" = queue.Queue()
_lock = threading.Lock()
_worker = None


def enqueue(run_id: int):
    if settings.GRADER_SYNC:
        process_run(run_id)
        return
    global _worker
    _q.put(run_id)
    with _lock:
        if _worker is None or not _worker.is_alive():
            _worker = threading.Thread(target=_loop, name="grader-worker", daemon=True)
            _worker.start()


def _loop():
    while True:
        run_id = _q.get()
        try:
            process_run(run_id)
        finally:
            close_old_connections()
            _q.task_done()


def _command(src: Path, rules: Path, out: Path, peers: Path | None = None):
    if settings.GRADER_USE_DOCKER:
        work = src.parent
        cmd = ["docker", "run", "--rm", "--network", "none", "--pids-limit", "256", "--memory", "1g",
               "-v", f"{work}:/work", settings.GRADER_DOCKER_IMAGE,
               "python", "grade.py", f"/work/{src.name}", "--rules", "/work/rules.json",
               "--out-dir", "/work/out", "--quiet"]
        return cmd + (["--peers", f"/work/{peers.name}"] if peers else [])
    cmd = [sys.executable, str(REPO_ROOT / "grade.py"), str(src), "--rules", str(rules),
           "--out-dir", str(out), "--quiet"]
    return cmd + (["--peers", str(peers)] if peers else [])


def write_peers(sub, folder: Path) -> int:
    """Copy the latest submission of every other student for the same problem into `folder`
    as <username>.c. The student's own submissions are never included."""
    from .models import Submission
    latest = {}
    for other in (Submission.objects.filter(problem=sub.problem).exclude(student=sub.student)
                  .select_related("student").order_by("id")):
        latest[other.student.username] = other
    folder.mkdir(parents=True, exist_ok=True)
    written = 0
    for username, other in sorted(latest.items()):
        try:
            (folder / f"{username}.c").write_bytes(Path(other.file.path).read_bytes())
            written += 1
        except OSError:
            continue
    return written


def process_run(run_id: int):
    from .models import Flag, GradingRun, MetricResult
    run = GradingRun.objects.select_related("submission__ruleset", "submission__problem").get(pk=run_id)
    run.status, run.started_at = GradingRun.RUNNING, timezone.now()
    run.save(update_fields=["status", "started_at"])
    sub = run.submission
    tmp = Path(tempfile.mkdtemp(prefix="grade_job_"))
    try:
        name = Path(sub.original_name).name or "submission.c"
        src = tmp / (name if name.endswith(".c") else name + ".c")
        src.write_bytes(Path(sub.file.path).read_bytes())
        rules = tmp / "rules.json"
        rules.write_text(sub.ruleset.json_text, encoding="utf-8")
        out = tmp / "out"
        peers = None
        if settings.GRADER_COMPARE_PEERS:
            peers = tmp / "peers"
            write_peers(sub, peers)
        proc = subprocess.run(_command(src, rules, out, peers), cwd=REPO_ROOT, capture_output=True, text=True,
                              timeout=settings.GRADER_TIMEOUT_S)
        if proc.returncode != 0:
            raise RuntimeError((proc.stderr or proc.stdout or "grader failed").strip()[-1500:])
        report = json.loads((out / f"{src.stem}.json").read_text(encoding="utf-8"))
        run.report_json = json.dumps(report, sort_keys=True)
        run.report_txt = (out / f"{src.stem}.txt").read_text(encoding="utf-8")
        run.grade, run.partial = report["grade"], report["partial"]
        run.rules_hash, run.submission_hash = report["rules_hash"], report["submission_hash"]
        run.status = GradingRun.DONE
        run.metrics.all().delete()
        run.flags.all().delete()
        for m in report["metrics"]:
            MetricResult.objects.create(run=run, name=m["name"], analyzer=m.get("analyzer", ""),
                                        status=m["status"], score=m["score"], weight=m["weight"],
                                        contribution=m["contribution"], feedback=m["feedback"],
                                        evidence=m.get("evidence") or {})
        for f in report["flags"]:
            Flag.objects.create(run=run, kind=f.get("kind", "flag"), detail=f.get("detail", ""))
    except subprocess.TimeoutExpired:
        run.status, run.error = GradingRun.FAILED, f"grading exceeded {settings.GRADER_TIMEOUT_S}s"
    except Exception as e:  # noqa: BLE001 - a failed job must never kill the worker
        run.status, run.error = GradingRun.FAILED, f"{type(e).__name__}: {e}"[:1500]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        run.finished_at = timezone.now()
        run.save()
