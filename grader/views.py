import csv
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from . import services
from .forms import BulkUploadForm, RuleSetForm, UploadForm
from .models import Flag, GradingRun, Problem

staff_required = user_passes_test(lambda u: u.is_active and u.is_staff)


def _can_see(user, run):
    return user.is_staff or run.submission.student_id == user.id


@login_required
def problem_list(request):
    return render(request, "grader/problems.html", {"problems": Problem.objects.order_by("title")})


@login_required
def problem_upload(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        f = form.cleaned_data["file"]
        try:
            run = services.submit(request.user, problem, f.read(), f.name)
        except (services.RateLimited, ValueError) as e:
            form.add_error(None, str(e))
        else:
            return redirect("run_detail", run_id=run.id)
    history = GradingRun.objects.filter(submission__student=request.user, submission__problem=problem)[:10]
    return render(request, "grader/upload.html", {"problem": problem, "form": form, "history": history})


@login_required
def run_detail(request, run_id):
    run = get_object_or_404(GradingRun.objects.select_related("submission__problem", "submission__student"), pk=run_id)
    if not _can_see(request.user, run):
        raise Http404
    flags = run.flags.all()
    if not request.user.is_staff:                  # copy flags are for the instructor only
        flags = flags.exclude(kind__in=Flag.COPY_KINDS)
    return render(request, "grader/run_detail.html", {"run": run, "flags": flags,
                                                      "metrics": run.metrics.all()})


@login_required
def run_status(request, run_id):
    run = get_object_or_404(GradingRun, pk=run_id)
    if not _can_see(request.user, run):
        raise Http404
    return JsonResponse({"id": run.id, "status": run.status, "grade": run.grade, "partial": run.partial})


@login_required
def run_download(request, run_id, fmt):
    run = get_object_or_404(GradingRun, pk=run_id)
    if not _can_see(request.user, run) or run.status != GradingRun.DONE or fmt not in ("json", "txt"):
        raise Http404
    body, ctype = (run.report_json, "application/json") if fmt == "json" else (run.report_txt, "text/plain")
    resp = HttpResponse(body, content_type=f"{ctype}; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="run{run.id}.{fmt}"'
    return resp


@login_required
def history(request):
    runs = GradingRun.objects.filter(submission__student=request.user).select_related("submission__problem")[:50]
    return render(request, "grader/history.html", {"runs": runs})


# ------------------------------------------------------------------ instructor
def _latest_runs(problem):
    """Latest finished run per student, in username order (reproducible)."""
    latest = {}
    for run in GradingRun.objects.filter(submission__problem=problem, status=GradingRun.DONE) \
            .select_related("submission__student").order_by("id"):
        latest[run.submission.student.username] = run
    return [latest[k] for k in sorted(latest)]


@staff_required
def dashboard(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    form = BulkUploadForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        try:
            runs = services.bulk_submit(request.user, problem, form.cleaned_data["archive"].read())
            messages.success(request, f"{len(runs)} submissions graded.")
        except Exception as e:  # noqa: BLE001
            messages.error(request, f"Bulk upload failed: {type(e).__name__}: {e}")
        return redirect("dashboard", slug=slug)
    runs = _latest_runs(problem)
    names = []
    for r in runs:
        for m in r.metrics.all():
            if m.name not in names:
                names.append(m.name)
    rows = []
    for r in runs:
        sc = {m.name: m.score for m in r.metrics.all()}
        rows.append({"run": r, "cells": [round(sc[n] * 100) if n in sc else None for n in names],
                     "flags": list(r.flags.all())})
    flagged = [(r["run"], f) for r in rows for f in r["flags"]]
    return render(request, "grader/dashboard.html", {"problem": problem, "rows": rows, "names": names,
                                                     "flagged": flagged, "form": form})


@staff_required
def dashboard_csv(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    runs = _latest_runs(problem)
    names = []
    for r in runs:
        for m in r.metrics.all():
            if m.name not in names:
                names.append(m.name)
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = f'attachment; filename="{problem.slug}_grades.csv"'
    w = csv.writer(resp)
    w.writerow(["student", "grade", "partial", *names, "flags", "rules_hash", "submission_hash"])
    for r in runs:
        sc = {m.name: m.score for m in r.metrics.all()}
        w.writerow([r.submission.student.username, r.grade, r.partial, *[sc.get(n, "") for n in names],
                    ";".join(f.kind for f in r.flags.all()), r.rules_hash, r.submission_hash])
    return resp


@staff_required
def ruleset_edit(request, slug):
    problem = get_object_or_404(Problem, slug=slug)
    current = problem.active_ruleset()
    initial = {"json_text": current.json_text if current else ""}
    form = RuleSetForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        rs = services.create_ruleset(problem, form.cleaned_data["json_text"], request.user,
                                     form.cleaned_data["note"])
        messages.success(request, f"Saved as a new rule version ({rs.rules_hash[:15]}...). "
                                  "Earlier submissions keep the rules they were graded with.")
        return redirect("ruleset_edit", slug=slug)
    return render(request, "grader/ruleset_form.html",
                  {"problem": problem, "form": form, "versions": problem.rulesets.order_by("-id")[:10]})


@staff_required
@require_POST
def regrade(request, run_id):
    """Re-run a submission: a NEW GradingRun row, so reproducibility can be shown side by side."""
    old = get_object_or_404(GradingRun, pk=run_id)
    run = GradingRun.objects.create(submission=old.submission)
    from . import jobs
    jobs.enqueue(run.id)
    return redirect("run_detail", run_id=run.id)
