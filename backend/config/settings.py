import os
from pathlib import Path

from config.connection_store import Connection, load_connection
from config.database import DEFAULT_PORT, NO_DATABASE, mssql_database

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"Не задана переменная окружения {name}")
    return value


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env("DJANGO_DEBUG", "0") == "1"
APP_RELEASE = env("APP_RELEASE", "")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")

INSTALLED_APPS = [
    "config",
    "accounts",
    "access",
    "directory",
    "staff",
    "lunches",
    "journal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "config.middleware.SameOriginMiddleware",
    "config.middleware.SetupGateMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

STATE_DIR = env("STATE_DIR", str(BASE_DIR / "state"))
DB_CONFIG_FILE = os.path.join(STATE_DIR, "database.bin")
SETUP_CODE_FILE = os.path.join(STATE_DIR, "setup-code.sha256")
STORED_CONNECTION = load_connection(DB_CONFIG_FILE, SECRET_KEY)
DATABASE_CONFIGURED = STORED_CONNECTION is not None or "DB_PASSWORD" in os.environ
DATABASE_CONNECTION = STORED_CONNECTION or Connection(
    host=env("DB_HOST", "127.0.0.1"),
    port=env("DB_PORT", DEFAULT_PORT),
    name=env("DB_NAME", "obedy"),
    user=env("DB_USER", "obedy"),
    password=env("DB_PASSWORD", ""),
    trust_certificate=env("DB_TRUST_CERTIFICATE", "1") == "1",
)
DATABASES = {"default": mssql_database(DATABASE_CONNECTION, env("DB_TEST_NAME", "test_obedy")) if DATABASE_CONFIGURED else NO_DATABASE}

LANGUAGE_CODE = "ru"
TIME_ZONE = "Europe/Moscow"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

COOKIE_SECURE = env("COOKIE_SECURE", "0") == "1"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"django": {"handlers": ["console"], "level": "ERROR"}},
}
