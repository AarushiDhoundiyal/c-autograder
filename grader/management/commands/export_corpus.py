"""python manage.py export_corpus <problem-slug>  -> copy finished submissions into corpus/peers/<slug>/
so later submissions are compared with them. Run it AFTER a deadline, not while grading is under way."""
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
        dest = REPO_ROOT / "corpus" / "peers" / slug
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
