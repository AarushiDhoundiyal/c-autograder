import hashlib
import json
import uuid

from django.conf import settings
from django.db import models


def upload_path(instance, filename):
    return f"submissions/{uuid.uuid4().hex}.c"        # generated name: the student's name is never used


class Problem(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    spec = models.TextField(blank=True, help_text="Markdown/plain text shown to students")
    sample_input = models.TextField(blank=True)

    def __str__(self):
        return self.title

    def active_ruleset(self):
        return self.rulesets.order_by("-created_at", "-id").first()


class RuleSet(models.Model):
    """A versioned rules file. Never edited in place: saving the editor creates a new row."""
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="rulesets")
    json_text = models.TextField()
    rules_hash = models.CharField(max_length=80, blank=True)
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.problem.slug} rules {self.rules_hash[:15]}"


class Submission(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="submissions")
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name="submissions")
    ruleset = models.ForeignKey(RuleSet, on_delete=models.PROTECT)
    file = models.FileField(upload_to=upload_path)
    original_name = models.CharField(max_length=100, default="submission.c")
    sha256 = models.CharField(max_length=80, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def compute_hash(self, data: bytes):
        self.sha256 = "sha256:" + hashlib.sha256(data).hexdigest()


class GradingRun(models.Model):
    QUEUED, RUNNING, DONE, FAILED = "queued", "running", "done", "failed"
    STATUSES = [(s, s) for s in (QUEUED, RUNNING, DONE, FAILED)]
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name="runs")
    status = models.CharField(max_length=10, choices=STATUSES, default=QUEUED)
    grade = models.FloatField(null=True, blank=True)
    partial = models.BooleanField(default=False)
    rules_hash = models.CharField(max_length=80, blank=True)
    submission_hash = models.CharField(max_length=80, blank=True)
    report_json = models.TextField(blank=True)
    report_txt = models.TextField(blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    @property
    def report(self):
        try:
            return json.loads(self.report_json)
        except ValueError:
            return None

    @property
    def failing_cases(self):
        out = []
        for m in (self.report or {}).get("metrics", []):
            out += m.get("evidence", {}).get("failing", []) if isinstance(m.get("evidence"), dict) else []
        return out[:6]

    @property
    def suggestions(self):
        seen, out = set(), []
        for m in (self.report or {}).get("metrics", []):
            for s in m.get("suggestions", []):
                if s not in seen:
                    seen.add(s)
                    out.append(s)
        return out


class MetricResult(models.Model):
    run = models.ForeignKey(GradingRun, on_delete=models.CASCADE, related_name="metrics")
    name = models.CharField(max_length=60)
    analyzer = models.CharField(max_length=60, blank=True)
    status = models.CharField(max_length=10, default="ok")
    score = models.FloatField(default=0)
    weight = models.FloatField(default=0)
    contribution = models.FloatField(default=0)
    feedback = models.TextField(blank=True)
    evidence = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["id"]


class Flag(models.Model):
    """Suspicion flag for the instructor to review (a request for review, never a verdict)."""
    run = models.ForeignKey(GradingRun, on_delete=models.CASCADE, related_name="flags")
    kind = models.CharField(max_length=40)
    detail = models.TextField(blank=True)

    COPY_KINDS = ("similarity", "llm_copy", "online_copy")
