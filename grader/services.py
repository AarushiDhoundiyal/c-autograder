"""Shared logic for the HTML views and the JSON API."""
import io
import json
import zipfile
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.utils import timezone

from agent.rules import canonical_hash
from . import jobs
from .models import GradingRun, RuleSet, Submission


class RateLimited(Exception):
    pass


def check_rate_limit(user):
    active = GradingRun.objects.filter(submission__student=user,
                                       status__in=[GradingRun.QUEUED, GradingRun.RUNNING]).count()
    if active >= settings.MAX_ACTIVE_JOBS_PER_USER:
        raise RateLimited("You already have several submissions waiting. Please wait for them to finish.")
    recent = Submission.objects.filter(student=user, uploaded_at__gte=timezone.now() - timedelta(minutes=1)).count()
    if recent >= settings.MAX_SUBMISSIONS_PER_MINUTE:
        raise RateLimited("Too many uploads in a minute. Please slow down.")


def create_ruleset(problem, json_text, user=None, note=""):
    return RuleSet.objects.create(problem=problem, json_text=json_text, note=note, created_by=user,
                                  rules_hash=canonical_hash(json.loads(json_text)))


def submit(user, problem, data: bytes, original_name="submission.c", enqueue=True, check=True):
    ruleset = problem.active_ruleset()
    if ruleset is None:
        raise ValueError("This problem has no rules yet.")
    if check:
        check_rate_limit(user)
    sub = Submission(student=user, problem=problem, ruleset=ruleset,
                     original_name=Path(original_name).name[:100] or "submission.c")
    sub.compute_hash(data)
    sub.file.save("x.c", ContentFile(data), save=False)
    sub.save()
    run = GradingRun.objects.create(submission=sub)
    if enqueue:
        jobs.enqueue(run.id)
    return run


def bulk_submit(instructor, problem, archive_bytes: bytes, limit=500):
    """ZIP of <username>.c files. Unknown usernames are created (no usable password)."""
    User = get_user_model()
    runs = []
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as z:
        infos = [i for i in z.infolist() if not i.is_dir() and i.filename.lower().endswith(".c")]
        for info in sorted(infos, key=lambda i: i.filename)[:limit]:
            if info.file_size > settings.MAX_UPLOAD_BYTES:
                continue
            base = Path(info.filename).name            # never trust paths inside the archive
            username = Path(base).stem[:150]
            user, created = User.objects.get_or_create(username=username)
            if created:
                user.set_unusable_password()
                user.save()
            runs.append(submit(user, problem, z.read(info), base, check=False))
    return runs
