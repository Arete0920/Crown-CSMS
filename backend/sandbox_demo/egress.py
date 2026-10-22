"""Fail-closed external communications boundary for the synthetic Heritage school.

The full evaluator-host lockdown is an explicit setting on every API/worker
process. The Heritage tenant is blocked regardless of that flag.
"""
from __future__ import annotations

import os

from django.conf import settings

HERITAGE_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
SUPPRESSED_REASON = "sandbox_external_egress_suppressed"


class SandboxEgressSuppressed(RuntimeError):
    """External delivery was suppressed before provider I/O."""


def _school_id(value) -> str:
    if value is None:
        return ""
    for attr in ("school_id", "pk", "id"):
        if hasattr(value, attr):
            candidate = getattr(value, attr)
            if candidate is not None:
                return str(candidate).strip().lower()
    return str(value).strip().lower()


def _is_heritage_school(school_id: str) -> bool:
    configured = str(getattr(settings, "CROWN_DEMO_SCHOOL_ID", "") or "").strip().lower()
    return bool(school_id) and school_id in {HERITAGE_SCHOOL_ID, configured}


def sandbox_external_egress_blocked(*, school_id=None, sender=None, recipient=None) -> bool:
    """Deny evaluator-host traffic and synthetic Heritage provider delivery."""
    for flag in ("CROWN_SANDBOX_OUTBOUND_DISABLED", "CROWN_SANDBOX_EVALUATOR_MODE"):
        configured = getattr(settings, flag, False)
        environment = os.getenv(flag, "")
        if configured is True or str(configured).strip().lower() in {"1", "true", "yes", "on"}:
            return True
        if environment.strip().lower() in {"1", "true", "yes", "on"}:
            return True

    for candidate in (school_id, sender, recipient):
        if _is_heritage_school(_school_id(candidate)):
            return True

    from core.tenant_models import get_current_school

    return _is_heritage_school(_school_id(get_current_school()))


def require_external_egress(channel: str, *, school_id=None, sender=None, recipient=None) -> None:
    """Reject external provider use before acquiring credentials or performing I/O."""
    if sandbox_external_egress_blocked(
        school_id=school_id, sender=sender, recipient=recipient
    ):
        raise SandboxEgressSuppressed(SUPPRESSED_REASON)
