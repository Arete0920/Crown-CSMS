"""Fail-closed isolation for legacy fictional-school management commands.

These commands are not the hosted Heritage sandbox entrypoint. They must never
modify data on hosted, Azure, or explicitly production-tagged applications.
"""

from __future__ import annotations

import os

from django.conf import settings
from django.core.management.base import CommandError


_PRODUCTION_LABELS = frozenset({"prod", "production", "live"})
_LOCAL_CONTEXT_LABELS = frozenset({"local", "test", "testing", "dev", "development", "ci", "pytest"})
_ENVIRONMENT_KEYS = (
    "CROWN_ENV",
    "DJANGO_ENV",
    "ENVIRONMENT",
    "APP_ENV",
    "AZURE_ENVIRONMENT",
)


def require_local_demo_seed(*, operation: str) -> None:
    """Reject legacy demo writes on production-tagged or hosted environments."""
    # Local labeling does not override a conflicting hosted, staging, or
    # production environment. Honor both process and resolved settings.
    labels = {
        str(value).strip().lower()
        for key in _ENVIRONMENT_KEYS
        for value in (os.getenv(key), getattr(settings, key, None))
        if value is not None and str(value).strip()
    }
    if labels & _PRODUCTION_LABELS:
        raise CommandError(f"{operation}: prohibited in a production environment")
    if labels - _LOCAL_CONTEXT_LABELS:
        raise CommandError(f"{operation}: prohibited with a non-local environment marker")
    if any(
        os.getenv(key) or getattr(settings, key, None)
        for key in ("WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "WEBSITE_SITE_NAME", "AZURE_ENVIRONMENT")
    ):
        raise CommandError(f"{operation}: prohibited in hosted environments")

    # A missing or incorrectly labeled environment is not proof of isolation.
    if os.getenv("CROWN_ENV", "").strip().lower() not in {"local", "test"}:
        raise CommandError(f"{operation}: CROWN_ENV=local or test is required")
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        raise CommandError(f"{operation}: isolated local SQLite is required")


def require_local_demo_wipe(*, school_name: str, confirmed: bool) -> None:
    """Allow destructive resets only with positive local-demo evidence."""
    require_local_demo_seed(operation="school wipe")
    if school_name != "Heritage Christian Academy":
        raise CommandError("Destructive resets are limited to Heritage Christian Academy")
    if not confirmed:
        raise CommandError("--confirm-demo-wipe is required with --wipe")
    if os.getenv("CROWN_ALLOW_DEMO_WIPE", "").strip().lower() != "true":
        raise CommandError("CROWN_ALLOW_DEMO_WIPE=true is required for destructive resets")
    if (os.getenv("CROWN_ENV", "").strip().lower() not in {"local", "test"}):
        raise CommandError("Destructive demo resets require CROWN_ENV=local or test")
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        raise CommandError("Destructive demo reset refused: database is not local SQLite")
