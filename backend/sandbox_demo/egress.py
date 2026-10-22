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


def _unscoped_heritage_user(value) -> bool:
    """Deny unscoped direct sends from users affiliated with Heritage.

    UserAccount.school is optional: legitimate identities may be attached only
    through UserRole. Without a tenant context, silently treating their user
    UUID as a school UUID would bypass the unconditional Heritage quarantine.
    """
    from core.models import UserAccount, UserRole

    if not isinstance(value, UserAccount) or value.pk is None:
        return False
    configured = str(getattr(settings, "CROWN_DEMO_SCHOOL_ID", "") or "").strip().lower()
    school_ids = [HERITAGE_SCHOOL_ID]
    if configured and configured != HERITAGE_SCHOOL_ID:
        school_ids.append(configured)
    # Database errors propagate: a failed ownership check must not allow I/O.
    return UserRole.objects.filter(user_id=value.pk, school_id__in=school_ids).exists()


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

    current_school = get_current_school()
    if _is_heritage_school(_school_id(current_school)):
        return True
    # Explicit authorized school context takes precedence for shared users.
    # Without it, check memberships that are not represented by the nullable
    # UserAccount.school FK before any provider token or transport is touched.
    if current_school is None:
        return any(_unscoped_heritage_user(value) for value in (sender, recipient))
    return False


def require_external_egress(channel: str, *, school_id=None, sender=None, recipient=None) -> None:
    """Reject external provider use before acquiring credentials or performing I/O."""
    if sandbox_external_egress_blocked(
        school_id=school_id, sender=sender, recipient=recipient
    ):
        raise SandboxEgressSuppressed(SUPPRESSED_REASON)
