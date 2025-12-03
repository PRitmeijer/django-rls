"""
PostgreSQL test settings (redundant - kept for backwards compatibility).

Note: The default settings.py now uses PostgreSQL by default.
This file is kept for backwards compatibility but is no longer needed.
"""
import os
from django_rls.settings_type import DjangoRLSSettings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = "fake-key"
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_rls",
    "tests.testproject.app",
    "tests.testproject.regular_app",  # NOT in TENANT_APPS - should not get RLS
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_rls.middleware.RLSMiddleware",
]

ROOT_URLCONF = "tests.testproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# PostgreSQL database configuration
# Tests should use the runtime user (not migration user) to properly test RLS enforcement
# The runtime user is subject to RLS policies, while the migration user has BYPASSRLS
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "testdb"),
        # Use runtime user for tests to ensure RLS policies are enforced
        # Migration user (testmigrate) has BYPASSRLS and would bypass RLS
        "USER": os.environ.get("POSTGRES_RUNTIME_USER", os.environ.get("POSTGRES_USER", "testuser")),
        "PASSWORD": os.environ.get("POSTGRES_RUNTIME_PASSWORD", os.environ.get("POSTGRES_PASSWORD", "testuserpass")),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

STATIC_URL = "/static/"

# Django RLS Configuration
DJANGO_RLS = DjangoRLSSettings(
    RLS_FIELDS=["tenant_id", "user_id"],
    TENANT_APPS=["test_app"],  # Use the app label "test_app" as defined in apps.py
)

