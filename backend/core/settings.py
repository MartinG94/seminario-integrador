"""
Django settings for the SGD-AVEIT backend (Spec 001 — Walking Skeleton).

Configuration values that vary between environments (secrets, database
credentials, debug flag) are read from environment variables / a local
`.env` file, never hardcoded. See `.env.example` for the expected keys.
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = os.environ.get("DEBUG", "0") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "accounts",
    "socios",
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

ROOT_URLCONF = "core.urls"

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

WSGI_APPLICATION = "core.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("DATABASE_NAME", "aveit_tribunal_dev"),
        "USER": os.environ.get("DATABASE_USER", "aveit_dev"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", "aveit_dev_password_2026"),
        "HOST": os.environ.get("DATABASE_HOST", "localhost"),
        "PORT": os.environ.get("DATABASE_PORT", "3306"),
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# PBKDF2 (Django default, first in the list) satisfies RNF-04 without adding
# a third-party hashing dependency (Argon2 would require `argon2-cffi`).
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Cordoba"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Deny by default (CA3): every endpoint must opt in to anonymous access
    # explicitly instead of opting out of authentication.
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# RNF-04 / CA4: la sesión tiene duración limitada y un token vencido no da
# acceso a ningún recurso protegido.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# LOGGING: a dedicated, non-propagating "security" logger is the audit trail
# required by CA4. Handlers/formatters here must never be given the raw
# request body, password fields or full tokens — only the event name, the
# username/legajo, the outcome and a timestamp (see accounts.audit, added in
# the RBAC task).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "audit": {
            "format": "%(asctime)s level=%(levelname)s logger=%(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "audit",
        },
    },
    "loggers": {
        "security": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
