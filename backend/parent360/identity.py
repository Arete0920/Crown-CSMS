from __future__ import annotations

from typing import Any

from households.models import Guardian, Household


class Parent360IdentityError(Exception):
    """Raised when a caller cannot be resolved to one active tenant-safe household."""


def resolve_household_for_account(user: Any) -> Household:
    """Resolve Parent360 access only through the canonical Guardian.account link.

    Email matching is intentionally excluded. Missing, inactive, cross-school, and
    inconsistent relationships fail closed.
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
        raise Parent360IdentityError("guardian_account_link_required")

    household = guardian.household
    if guardian.school_id != household.school_id:
        raise Parent360IdentityError("guardian_household_tenant_mismatch")
    if str(guardian.school_id) != str(school_id):
        raise Parent360IdentityError("account_guardian_tenant_mismatch")
    if not household.is_active:
        raise Parent360IdentityError("inactive_household")

    return household
