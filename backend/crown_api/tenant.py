# backend/crown_api/tenant.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

TENANT_HEADER = "HTTP_X_SCHOOL_ID"  # Django stores headers as HTTP_*
TENANT_HEADER_LEGACY = "HTTP_X_CROWN_SCHOOL_ID"  # Legacy alias
TENANT_ATTR = "tenant_school_id"


@dataclass(frozen=True)
class TenantResolution:
    school_id: Optional[UUID]
    source: str  # "header" | "header_invalid" | "user" | "drf_force" | "none"
    header_present: bool = False  # True if X-School-Id header was supplied (valid or invalid)


def _parse_uuid(value: str) -> Optional[UUID]:
    try:
        return UUID(str(value).strip())
    except Exception:
        return None


def _get_tenant_header(request) -> Optional[str]:
    """
    Extract tenant header from request.
    Canonical first, then legacy for backward compatibility.
    """
    # Django test client uses HTTP_ prefix
    return (
        request.META.get(TENANT_HEADER)
        or request.META.get(TENANT_HEADER_LEGACY)
    )


def resolve_tenant_school_id(request) -> TenantResolution:
    """
    Single source of truth for tenant resolution.

    Priority:
    1) X-School-Id header (canonical + legacy) — ALWAYS wins if present
    2) Authenticated user / JWT-derived user with school_id attribute
    3) DRF test client force_authenticate() (request._force_auth_user)
    4) None
    
    CRITICAL: If header is present but invalid UUID, mark as "header_invalid"
    so scoping layer returns 400, not 500.
    """
    # 1) HEADER PATH — WINS if present (even if invalid)
    raw_header = _get_tenant_header(request)
    if raw_header is not None:
        parsed = _parse_uuid(raw_header)
        if not parsed:
            # Header present but invalid UUID → mark for scoping to return 400
            return TenantResolution(school_id=None, source="header_invalid", header_present=True)
        return TenantResolution(school_id=parsed, source="header", header_present=True)

    # 2) Authenticated user path (JWT middleware sets this)
    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        user_school_id = getattr(user, "school_id", None)
        if user_school_id:
            parsed = _parse_uuid(str(user_school_id))
            if parsed:
                return TenantResolution(school_id=parsed, source="user", header_present=False)

    # 3) DRF test client force_authenticate() path
    # APIClient.force_authenticate sets request._force_auth_user before the view runs.
    force_user = getattr(request, "_force_auth_user", None)
    if force_user is not None:
        user_school_id = getattr(force_user, "school_id", None)
        if user_school_id:
            parsed = _parse_uuid(str(user_school_id))
            if parsed:
                return TenantResolution(school_id=parsed, source="drf_force", header_present=False)

    # 4) No tenant found
    return TenantResolution(school_id=None, source="none", header_present=False)


def get_tenant_school_id(request, *, required: bool = True) -> Optional[UUID]:
    """
    Returns the resolved tenant school_id (UUID) from request.<tenant attr>.
    If not present, resolves and stamps it.

    If required=True and cannot resolve, raises PermissionError (handled upstream).
    """
    existing = getattr(request, TENANT_ATTR, None)
    if existing:
        return existing

    res = resolve_tenant_school_id(request)
    setattr(request, TENANT_ATTR, res.school_id)

    if required and not res.school_id:
        raise PermissionError("TENANT_REQUIRED")

    return res.school_id

    return res.school_id
