from django.contrib.auth import views as auth_views
from django.urls import path

from . import api, views

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.problem_list, name="problems"),
    path("problems/<slug:slug>/", views.problem_upload, name="problem_upload"),
    path("history/", views.history, name="history"),
    path("runs/<int:run_id>/", views.run_detail, name="run_detail"),
    path("runs/<int:run_id>/status/", views.run_status, name="run_status"),
    path("runs/<int:run_id>/download/<str:fmt>/", views.run_download, name="run_download"),
    path("runs/<int:run_id>/regrade/", views.regrade, name="regrade"),
    path("instructor/<slug:slug>/", views.dashboard, name="dashboard"),
    path("instructor/<slug:slug>/grades.csv", views.dashboard_csv, name="dashboard_csv"),
    path("instructor/<slug:slug>/rules/", views.ruleset_edit, name="ruleset_edit"),
    path("api/submissions/", api.submissions, name="api_submissions"),
    path("api/runs/<int:run_id>/", api.run_detail, name="api_run"),
]
