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

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables desde .env si existe (en la raíz del proyecto o en backend)
load_dotenv(BASE_DIR.parent / ".env")
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = (
    os.getenv("DJANGO_SECRET_KEY")
    or "django-insecure-sgd-aveit-dev-secret-key-replace-in-production-2026"
)

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "t")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,backend,testserver").split(
        ","
    )
    if host.strip()
]

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Dependencias de terceros
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    # Módulos del núcleo
    "core",
    "accounts",
    "socios",
    # Módulos funcionales
    "padron",
    "ranking",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
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
ASGI_APPLICATION = "core.asgi.application"

# Database — MySQL 8.0 (con fallback opcional a SQLite para desarrollo desacoplado)
USE_SQLITE = os.getenv("USE_SQLITE", "False").lower() in ("true", "1", "t")

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / os.getenv("SQLITE_DATABASE_NAME", "db.sqlite3"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DATABASE_NAME", os.getenv("MYSQL_DATABASE", "aveit_tribunal_dev")),
            "USER": os.getenv("DATABASE_USER", os.getenv("MYSQL_USER", "aveit_dev")),
            "PASSWORD": os.getenv(
                "DATABASE_PASSWORD", os.getenv("MYSQL_PASSWORD", "aveit_dev_password_2026")
            ),
            "HOST": os.getenv("DATABASE_HOST", os.getenv("MYSQL_HOST", "db")),
            "PORT": os.getenv("DATABASE_PORT", os.getenv("MYSQL_PORT", "3306")),
            "OPTIONS": {
                "charset": "utf8mb4",
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
                "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "3")),
                "read_timeout": int(os.getenv("DB_READ_TIMEOUT", "3")),
            },
        }
    }

# Password validation
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

# Internationalization
LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Deny by default (CA3): every endpoint must opt in to anonymous access
    # explicitly instead of opting out of authentication.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

# SimpleJWT Configuration
# RNF-04 / CA4: la sesión tiene duración limitada y un token vencido no da
# acceso a ningún recurso protegido.
JWT_SECRET = os.getenv("JWT_SIGNING_KEY") or SECRET_KEY
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_LIFETIME_MINUTES") or "60")
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=int(os.getenv("JWT_REFRESH_TOKEN_LIFETIME_DAYS") or "7")
    ),
    "SIGNING_KEY": JWT_SECRET,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:4200,http://127.0.0.1:4200",
    ).split(",")
    if origin.strip()
]

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
