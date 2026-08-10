from __future__ import annotations

import os
from typing import Any

from households.models import Guardian, Household


class Parent360IdentityError(Exception):
    """Raised when a caller cannot be resolved to one active tenant-safe household."""


def _sandbox_parent_household(user: Any, school_id: Any) -> Household | None:
    """Resolve the deterministic Heritage sandbox parent without weakening production auth.

    The public admissions flow creates a new canonical ``households.Household`` for
    each submission. The flagship sandbox parent account is intentionally created
    before that application exists, so it cannot carry a Guardian.account link to
    the newly created household at seed time. In the explicitly enabled open-session
    sandbox only, bind the known Heritage parent persona to the newest Reed Family
    application household. Production and every other account remain fail closed.
    """
    sandbox_open = str(os.getenv("CROWN_SANDBOX_ALLOW_OPEN_SESSION", "0")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not sandbox_open:
        return None

    email = str(getattr(user, "email", "") or "").strip().lower()
    if email != "parent.reed@heritage.example.org":
        return None

    try:
        from applications.models import Application
    except Exception:
        return None

    application = (
        Application.objects.select_related("household")
        .filter(
            school_id=school_id,
            household__school_id=school_id,
            household__name="Reed Family",
        )
        .order_by("-created_at")
        .first()
    )
    if application is None:
        return None

    household = application.household
    if not household.is_active or str(household.school_id) != str(school_id):
        return None
    return household


def resolve_household_for_account(user: Any) -> Household:
    """Resolve Parent360 access through canonical account identity.

    Production authorization requires the canonical ``Guardian.account`` link.
    A narrowly scoped exception exists only when the explicit open-session sandbox
    is enabled for the fixed Heritage parent persona; that exception resolves only
    the tenant-matched Reed Family application household created by the real demo
    admissions transaction.
    """
    if user is None or not getattr(user, "is_authenticated", False):
        raise Parent360IdentityError("authenticated_account_required")
    if not getattr(user, "is_active", False):
        raise Parent360IdentityError("inactive_account")

    school_id = getattr(user, "school_id", None)
    if school_id in (None, ""):
        raise Parent360IdentityError("account_tenant_required")

    guardian = (
        Guardian.objects.select_related("household", "account")
        .filter(account_id=user.pk, school_id=school_id)
        .first()
    )
    if guardian is None:
        sandbox_household = _sandbox_parent_household(user, school_id)
        if sandbox_household is not None:
            return sandbox_household
        raise Parent360IdentityError("guardian_account_link_required")

    household = guardian.household
    if guardian.school_id != household.school_id:
        raise Parent360IdentityError("guardian_household_tenant_mismatch")
    if str(guardian.school_id) != str(school_id):
        raise Parent360IdentityError("account_guardian_tenant_mismatch")
    if not household.is_active:
        raise Parent360IdentityError("inactive_household")

    return household
