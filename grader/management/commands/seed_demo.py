"""python manage.py seed_demo  -> users (teacher/teacher123, student1/student123) + every problem with its rules."""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from agent import REPO_ROOT
from grader import services
from grader.models import Problem

PROBLEMS = [("add", "Add two integers", "7 5\n"),
            ("sum_array", "Sum of an array", "3\n1 2 3\n"),
            ("climb_stairs", "Climbing stairs (dynamic programming)", "4\n"),
            ("knapsack", "0/1 knapsack (dynamic programming)", "3 50\n10 60\n20 100\n30 120\n"),
            ("lis", "Longest increasing subsequence (dynamic programming)", "8\n10 9 2 5 3 7 101 18\n"),
            ("hanoi", "Tower of Hanoi (recursion)", "2\n"),
            ("nqueens", "N-Queens (backtracking)", "4\n"),
            ("permutations", "All permutations (backtracking)", "3\n"),
            ("reverse_list", "Reverse a linked list", "5\n1 2 3 4 5\n"),
            ("balanced_brackets", "Balanced brackets (stack)", "{[()()]}\n"),
            ("count_occurrences", "Count occurrences of a target (arrays)", "6 2\n2 3 2 -1 2 0\n"),
            ("longest_run", "Longest run of identical characters (strings)", "aaabbccccdd\n"),
            ("linked_list_reverse", "Reverse a linked list, EMPTY for n = 0", "5\n1 2 3 4 5\n"),
            ("graph_components", "Connected components (graphs)", "5 3\n1 2\n2 3\n4 5\n"),
            ("stairs_dp", "Climbing stairs, n <= 1000 (dynamic programming)", "5\n")]


class Command(BaseCommand):
    help = "Create demo users, problems and rule sets (safe to run twice)."

    def handle(self, *a, **o):
        User = get_user_model()
        if not User.objects.filter(username="teacher").exists():
            User.objects.create_superuser("teacher", password="teacher123")
        if not User.objects.filter(username="student1").exists():
            User.objects.create_user("student1", password="student123")
        for slug, title, sample in PROBLEMS:
            spec = REPO_ROOT / "problems" / slug / "spec.md"
            rules = REPO_ROOT / "rules" / f"{slug}_full.json"
            p, _ = Problem.objects.get_or_create(slug=slug, defaults={
                "title": title, "spec": spec.read_text(encoding="utf-8"), "sample_input": sample})
            if p.rulesets.count() == 0:
                services.create_ruleset(p, rules.read_text(encoding="utf-8"),
                                        User.objects.get(username="teacher"), "initial rules")
        self.stdout.write(self.style.SUCCESS("Demo data ready: teacher/teacher123 (instructor), student1/student123"))
