"""python manage.py seed_demo  -> users (teacher/teacher123, student1/student123) + both problems with rules."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from agent import REPO_ROOT
from grader import services
from grader.models import Problem

PROBLEMS = [("add", "Add two integers", "problems/add/spec.md", "7 5\n", "rules/add_full.json"),
            ("sum_array", "Sum of an array", "problems/sum_array/spec.md", "3\n1 2 3\n", "rules/sum_array_full.json")]


class Command(BaseCommand):
    help = "Create demo users, problems and rule sets (safe to run twice)."

    def handle(self, *a, **o):
        User = get_user_model()
        if not User.objects.filter(username="teacher").exists():
            User.objects.create_superuser("teacher", password="teacher123")
        if not User.objects.filter(username="student1").exists():
            User.objects.create_user("student1", password="student123")
        for slug, title, spec, sample, rules in PROBLEMS:
            p, _ = Problem.objects.get_or_create(slug=slug, defaults={
                "title": title, "spec": (REPO_ROOT / spec).read_text(encoding="utf-8"), "sample_input": sample})
            if p.rulesets.count() == 0:
                services.create_ruleset(p, (REPO_ROOT / rules).read_text(encoding="utf-8"),
                                        User.objects.get(username="teacher"), "initial rules")
        self.stdout.write(self.style.SUCCESS("Demo data ready: teacher/teacher123 (instructor), student1/student123"))
