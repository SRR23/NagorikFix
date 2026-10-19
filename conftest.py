"""
Project-wide pytest setup.

Uses config.settings.development and local Postgres via DB_* variables.
DATABASE_URL is removed so pytest does not create a test database on a
remote host that may be present in .env.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_BASE_DIR = Path(__file__).resolve().parent
load_dotenv(_BASE_DIR / ".env")

os.environ.pop("DATABASE_URL", None)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

_db_host = (os.environ.get("DB_HOST") or "localhost").strip().lower()
if _db_host not in {"localhost", "127.0.0.1"}:
    raise RuntimeError(
        f"Refusing to run tests against remote DB_HOST={_db_host!r}. "
        "Set DB_HOST=localhost (or 127.0.0.1) for pytest."
    )


def pytest_load_initial_conftests(early_config, parser, args):
    """Runs before Django setup. Keep DATABASE_URL cleared."""
    os.environ.pop("DATABASE_URL", None)


import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def _test_runtime_settings(settings):
    """Keep tests off Redis and off the network."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "nagorikfix-tests",
        }
    }
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def citizen_user(db):
    from apps.accounts.models import User

    # USERNAME_FIELD is email — pass it as the first create_user argument.
    return User.objects.create_user(
        "citizen@example.com",
        password="testpass123",
        username="citizen1",
        role=User.Role.CITIZEN,
    )


@pytest.fixture
def road_category(db):
    from apps.reports.models import Category

    return Category.objects.create(
        name="Road",
        slug="road",
        sort_order=1,
    )
