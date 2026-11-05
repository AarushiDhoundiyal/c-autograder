"""python manage.py export_corpus <problem-slug>  -> copy finished submissions into
corpus/peers/<problem>/, where <problem> is the "problem" name of the active rules, so that a
later batch of students is compared with this one. Current classmates are compared with each
other automatically while grading; use this command at the end of a course to keep the batch."""
import json

from django.core.management.base import BaseCommand, CommandError

from agent import REPO_ROOT
from grader.models import GradingRun, Problem


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("slug")

    def handle(self, slug, **o):
        try:
            problem = Problem.objects.get(slug=slug)
        except Problem.DoesNotExist:
            raise CommandError("unknown problem")
        ruleset = problem.active_ruleset()
        name = json.loads(ruleset.json_text).get("problem", slug) if ruleset else slug
        dest = REPO_ROOT / "corpus" / "peers" / name
        dest.mkdir(parents=True, exist_ok=True)
        seen, n = set(), 0
        for run in GradingRun.objects.filter(submission__problem=problem, status="done").order_by("id"):
            sub = run.submission
            if sub.id in seen:
                continue
            seen.add(sub.id)
            (dest / f"{sub.student.username}_{sub.id}.c").write_bytes(open(sub.file.path, "rb").read())
            n += 1
        self.stdout.write(f"{n} file(s) written to {dest}")
