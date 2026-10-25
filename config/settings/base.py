import os
from pathlib import Path

from .sites import load_site

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SITE = load_site(os.environ.get("SITE", "academy"))

# Static build only: nothing is served by Django in production.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "static-build-not-secret")
DEBUG = os.environ.get("DJANGO_DEBUG", "") == "1"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", SITE.domain]

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "django_distill",
    "pages",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "themes" / SITE.theme / "templates",
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {"context_processors": ["pages.context_processors.site"]},
    }
]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "themes" / SITE.theme / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

PRISMIC_REPOSITORY = os.environ.get("PRISMIC_REPOSITORY", "thec3")
PRISMIC_ACCESS_TOKEN = os.environ.get("PRISMIC_ACCESS_TOKEN", "")

USE_TZ = True
TIME_ZONE = "Europe/London"
