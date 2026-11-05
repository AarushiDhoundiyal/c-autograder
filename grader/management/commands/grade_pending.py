"""python manage.py grade_pending  -> grade every run left 'queued' or 'running' (e.g. after a server restart)."""
from django.core.management.base import BaseCommand

from grader import jobs
from grader.models import GradingRun


class Command(BaseCommand):
    def handle(self, *a, **o):
        ids = list(GradingRun.objects.filter(status__in=["queued", "running"]).order_by("id").values_list("id", flat=True))
        for i in ids:
            jobs.process_run(i)
        self.stdout.write(f"{len(ids)} run(s) processed")
