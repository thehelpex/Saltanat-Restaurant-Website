import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SESSION_SECRET")
if not SECRET_KEY:
    raise ImproperlyConfigured("SESSION_SECRET must be configured for the Django API.")

DEBUG = os.environ.get("DJANGO_DEBUG", "").lower() == "true"

allowed_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "testserver", ".replit.dev", ".replit.app"}
for variable in ("REPLIT_DOMAINS", "REPLIT_DEV_DOMAIN"):
    for host in os.environ.get(variable, "").split(","):
        host = host.strip().split(":")[0]
        if host:
            allowed_hosts.add(host)
ALLOWED_HOSTS = sorted(allowed_hosts)

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise ImproperlyConfigured("DATABASE_URL must be configured for the Django API.")

DATABASES = {
    "default": dj_database_url.parse(
        database_url,
        conn_max_age=600,
        conn_health_checks=True,
    )
}

INSTALLED_APPS = [
    "rest_framework",
    "saltanat_api",
]

MIDDLEWARE = []
ROOT_URLCONF = "saltanat_api.urls"
WSGI_APPLICATION = "saltanat_api.wsgi.application"
ASGI_APPLICATION = "saltanat_api.asgi.application"

TEMPLATES = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
APPEND_SLASH = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
    "DEFAULT_EXCEPTION_HANDLER": "saltanat_api.exceptions.api_exception_handler",
    "UNAUTHENTICATED_USER": None,
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}