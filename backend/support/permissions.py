"""Explicit school-scoped support authority, independent of generic staff flags."""

from types import SimpleNamespace

from core.permissions import IsPlatformOperator, user_has_permission


def active_user(user) -> bool:
    """Reject missing, anonymous and disabled principals, even with forced auth."""
    return bool(user and user.is_authenticated and user.is_active)


def platform_operator(user) -> bool:
    """Reuse the canonical active, schoolless global-operator boundary."""
    return IsPlatformOperator().has_permission(SimpleNamespace(user=user), None)


def can_submit(user, school) -> bool:
    """Accept active members of this active school or its platform operator."""
    return bool(
        active_user(user)
        and school
        and school.is_active
        and (
            platform_operator(user)
            or user.school_id == school.pk
            or user.roles.filter(school=school).exists()
        )
    )


def can_manage(user, school) -> bool:
    """Require an explicit support-management grant in this school."""
    return bool(
        active_user(user)
        and school
        and school.is_active
        and (
            platform_operator(user)
            or user_has_permission(user, "support.manage", school=school)
        )
    )


def can_view_all(user, school) -> bool:
    """Read grants do not authorize resolution or access to other schools."""
    return bool(
        can_manage(user, school)
        or (
            active_user(user)
            and school
            and school.is_active
            and user_has_permission(user, "support.view", school=school)
        )
    )
