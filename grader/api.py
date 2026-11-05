"""Small JSON API (HTTP Basic or session auth):
   POST /api/submissions/  multipart: problem=<slug>, file=<.c>   -> {"run_id":..,"status":"queued"}
   GET  /api/runs/<id>/    -> status, grade, partial, report (when done)"""
import base64
import json

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from . import services
from .forms import UploadForm
from .models import GradingRun, Problem


def _user(request):
    if request.user.is_authenticated:
        return request.user
    h = request.META.get("HTTP_AUTHORIZATION", "")
    if h.startswith("Basic "):
        try:
            name, _, pw = base64.b64decode(h[6:]).decode().partition(":")
        except Exception:  # noqa: BLE001
            return None
        return authenticate(request, username=name, password=pw)
    return None


@csrf_exempt            # authenticated by Basic credentials; session users use the HTML views
def submissions(request):
    user = _user(request)
    if user is None:
        return JsonResponse({"error": "authentication required"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)
    try:
        problem = Problem.objects.get(slug=request.POST.get("problem", ""))
    except Problem.DoesNotExist:
        return JsonResponse({"error": "unknown problem"}, status=404)
    form = UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return JsonResponse({"error": form.errors.get_json_data()}, status=400)
    f = form.cleaned_data["file"]
    try:
        run = services.submit(user, problem, f.read(), f.name)
    except services.RateLimited as e:
        return JsonResponse({"error": str(e)}, status=429)
    except ValueError as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"run_id": run.id, "status": run.status}, status=202)


def run_detail(request, run_id):
    user = _user(request)
    if user is None:
        return JsonResponse({"error": "authentication required"}, status=401)
    try:
        run = GradingRun.objects.select_related("submission").get(pk=run_id)
    except GradingRun.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)
    if not (user.is_staff or run.submission.student_id == user.id):
        return JsonResponse({"error": "not found"}, status=404)
    body = {"run_id": run.id, "status": run.status, "grade": run.grade, "partial": run.partial,
            "rules_hash": run.rules_hash, "submission_hash": run.submission_hash, "error": run.error}
    if run.status == GradingRun.DONE:
        report = run.report
        if not user.is_staff and report:             # copy flags are for instructors only
            report["flags"] = [f for f in report["flags"] if f.get("kind") not in ("similarity", "llm_copy", "online_copy")]
        body["report"] = report
    return JsonResponse(body)
