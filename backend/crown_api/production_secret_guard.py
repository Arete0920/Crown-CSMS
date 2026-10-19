"""Fail-closed validation for production and deploy-check secret configuration."""

from __future__ import annotations

import os
import sys
from django.core.exceptions import ImproperlyConfigured

_TRUE_VALUES = {"1", "true", "yes", "on"}
_HARDENED_ENVS = {"sandbox", "staging", "production", "prod", "live"}


def _is_hardened_context(argv: list[str] | None = None) -> bool:
    args = sys.argv if argv is None else argv
    crown_env = os.getenv("CROWN_ENV", "").strip().lower()
    django_env = os.getenv("DJANGO_ENV", "").strip().lower()
    environment = os.getenv("ENVIRONMENT", "").strip().lower()
    azure_environment = os.getenv("AZURE_ENVIRONMENT", "").strip().lower()
    deploy_security = os.getenv("CROWN_DEPLOY_SECURITY", "").strip().lower() in _TRUE_VALUES
    azure_runtime = bool(os.getenv("WEBSITE_HOSTNAME") or os.getenv("WEBSITE_INSTANCE_ID"))
    deploy_check = "--deploy" in args
    return (
        deploy_security
        or crown_env in _HARDENED_ENVS
        or django_env in _HARDENED_ENVS
        or environment in _HARDENED_ENVS
        or azure_environment in _HARDENED_ENVS
        or azure_runtime
        or deploy_check
    )


def enforce_production_secret(argv: list[str] | None = None) -> None:
    """Reject missing, insecure, weak, or generated-fallback secrets in hardened contexts."""
    if not _is_hardened_context(argv):
        return

    secret = os.getenv("DJANGO_SECRET_KEY") or os.getenv("SECRET_KEY") or ""
    if (
        not secret
        or secret.startswith("django-insecure-")
        or len(secret) < 50
        or len(set(secret)) < 5
    ):
        raise ImproperlyConfigured(
            "A strong DJANGO_SECRET_KEY or SECRET_KEY is required in production, "
            "staging, sandbox hardening, Azure runtime, and django --deploy checks. "
            "CROWN will not generate an ephemeral replacement."
        )


def validate_database_runtime(
    database_url: str,
    *,
    hardened: bool,
    hosted: bool,
) -> None:
    """Fail closed before Django can select its local SQLite fallback.

    A deploy-check or explicitly hardened process must specify a database.
    Hosted, sandbox, staging, and production processes must not use SQLite;
    local and CI SQLite continue to be supported.
    """
    if hardened and not database_url:
        raise ImproperlyConfigured(
            "DATABASE_URL is required in hardened environments."
        )
    if hosted and database_url.lower().startswith(("sqlite:", "sqlite3:")):
        raise ImproperlyConfigured(
            "Hosted and staging/production database must not use SQLite."
        )
