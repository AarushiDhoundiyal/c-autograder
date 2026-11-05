"""Django settings for the AutoGrader web layer (development defaults; see README.md)."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent            # = repository root
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "grader",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "autograder_web.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages"]},
}]
WSGI_APPLICATION = "autograder_web.wsgi.application"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3",
                         "NAME": os.environ.get("AUTOGRADER_DB", str(BASE_DIR / "db.sqlite3"))}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE, TIME_ZONE, USE_TZ = "en-us", "UTC", True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL = "/login/", "/", "/login/"
MEDIA_ROOT = Path(os.environ.get("AUTOGRADER_MEDIA", str(BASE_DIR / "media")))

# ---- AutoGrader settings -------------------------------------------------------------
MAX_UPLOAD_BYTES = 100 * 1024            # a single .c file
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
MAX_ACTIVE_JOBS_PER_USER = 3             # queued + running runs per student (rate limit)
MAX_SUBMISSIONS_PER_MINUTE = 10
GRADER_TIMEOUT_S = 300                   # hard limit for one grading job
GRADER_SYNC = os.environ.get("GRADER_SYNC", "0") == "1"     # run jobs inline (tests / debugging)
GRADER_USE_DOCKER = os.environ.get("GRADER_USE_DOCKER", "0") == "1"
GRADER_DOCKER_IMAGE = os.environ.get("GRADER_DOCKER_IMAGE", "c-autograder")
GRADER_COMPARE_PEERS = os.environ.get("GRADER_COMPARE_PEERS", "1") == "1"   # compare with classmates' submissions
