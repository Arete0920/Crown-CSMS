# backend/crown_api/tenant.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

TENANT_HEADER = "HTTP_X_SCHOOL_ID"
TENANT_HEADER_LEGACY = "HTTP_X_CROWN_SCHOOL_ID"
TENANT_ATTR = "tenant_school_id"
CANONICAL_TENANT_ATTR = "crown_tenant"
TENANT_OVERRIDE_PERMISSION = "core.override_tenant_context"


@dataclass(frozen=True)
class TenantResolution:
    school_id: Optional[UUID]
    source: str
    header_present: bool = False


@dataclass(frozen=True)
class TenantContext:
    """Immutable request tenant contract used during the staged middleware migration."""

    school_id: Optional[UUID]
    school: Optional[object]
    source: str
    header_present: bool
    principal_school_id: Optional[UUID]
    override_requested: bool
    override_authorized: bool
    actor_type: str


def _parse_uuid(value: object) -> Optional[UUID]:
    try:
        return UUID(str(value).strip())
    except Exception:
        return None


def _get_tenant_header(request) -> Optional[str]:
    return request.META.get(TENANT_HEADER) or request.META.get(TENANT_HEADER_LEGACY)


def _authenticated_principal(request):
    force_user = getattr(request, "_force_auth_user", None)
    user = getattr(request, "user", None)

    # DRF's APIClient.force_authenticate() stamps _force_auth_user before
    # Django's AuthenticationMiddleware may later expose the same principal as
    # request.user. Preserve the explicit fixture actor type in either shape.
    if force_user is not None and getattr(force_user, "is_authenticated", False):
        if user is None or not getattr(user, "is_authenticated", False) or user is force_user:
            return force_user, "drf_force"

    if user is not None and getattr(user, "is_authenticated", False):
        return user, "user"

    return None, "anonymous"


def _principal_school_id(principal) -> Optional[UUID]:
    """Resolve a principal's unambiguous school without granting cross-school authority.

    Direct UserAccount.school remains primary. A user whose direct school is unset may
    inherit a school only when all persisted UserRole memberships point to exactly one
    school. Multi-school role memberships remain ambiguous and require an explicit,
    authorized tenant override.
    """
    if principal is None or not getattr(principal, "is_authenticated", False):
        return None

    direct = _parse_uuid(getattr(principal, "school_id", None))
    if direct:
        return direct

    roles = getattr(principal, "roles", None)
    if roles is None:
        return None

    try:
        school_ids = list(
            roles.exclude(school_id__isnull=True)
            .values_list("school_id", flat=True)
            .distinct()[:2]
        )
    except Exception:
        return None

    if len(school_ids) == 1:
        return _parse_uuid(school_ids[0])
    return None


def principal_can_override_tenant(principal) -> bool:
    """Require explicit cross-school authority; ordinary staff status is insufficient."""
    if principal is None or not getattr(principal, "is_authenticated", False):
        return False
    if getattr(principal, "is_superuser", False):
        return True

    has_perm = getattr(principal, "has_perm", None)
    if callable(has_perm):
        try:
            if has_perm(TENANT_OVERRIDE_PERMISSION):
                return True
        except Exception:
            pass

    roles = getattr(principal, "roles", None)
    if roles is not None:
        try:
            if roles.filter(role_code="SUPPORT").exists():
                return True
        except Exception:
            pass

    staff_profile = getattr(principal, "staff", None)
    return bool(staff_profile and getattr(staff_profile, "role_type", None) == "SUPPORT")


def resolve_tenant_school_id(request) -> TenantResolution:
    """Resolve the requested tenant identifier without authorizing cross-school access."""
    raw_header = _get_tenant_header(request)
    if raw_header is not None:
        parsed = _parse_uuid(raw_header)
        if not parsed:
            return TenantResolution(school_id=None, source="header_invalid", header_present=True)
        return TenantResolution(school_id=parsed, source="header", header_present=True)

    user = getattr(request, "user", None)
    if user is not None and getattr(user, "is_authenticated", False):
        parsed = _principal_school_id(user)
        if parsed:
            source = "user" if _parse_uuid(getattr(user, "school_id", None)) else "user_role"
            return TenantResolution(school_id=parsed, source=source, header_present=False)

    force_user = getattr(request, "_force_auth_user", None)
    if force_user is not None:
        parsed = _principal_school_id(force_user)
        if parsed:
            source = "drf_force" if _parse_uuid(getattr(force_user, "school_id", None)) else "drf_force_role"
            return TenantResolution(school_id=parsed, source=source, header_present=False)

    return TenantResolution(school_id=None, source="none", header_present=False)


def build_tenant_context(request, *, school=None) -> TenantContext:
    """Build canonical tenant context while preserving resolver compatibility."""
    resolution = resolve_tenant_school_id(request)
    principal, actor_type = _authenticated_principal(request)
    principal_school_id = _principal_school_id(principal)

    drf_force_fixture_selection = bool(
        actor_type == "drf_force"
        and principal_school_id is None
        and getattr(request, "_force_auth_user", None) is principal
    )

    override_requested = bool(
        resolution.header_present
        and resolution.school_id
        and principal
        and resolution.school_id != principal_school_id
        and not drf_force_fixture_selection
    )
    override_authorized = bool(
        override_requested and principal_can_override_tenant(principal)
    )

    return TenantContext(
        school_id=resolution.school_id,
        school=school,
        source=resolution.source,
        header_present=resolution.header_present,
        principal_school_id=principal_school_id,
        override_requested=override_requested,
        override_authorized=override_authorized,
        actor_type=actor_type,
    )


def bind_tenant_context(request, context: TenantContext) -> TenantContext:
    """Stamp canonical and legacy request attributes from one context object."""
    setattr(request, CANONICAL_TENANT_ATTR, context)
    setattr(request, TENANT_ATTR, context.school_id)
    setattr(request, "_tenant_resolution_source", context.source)
    setattr(request, "_tenant_header_present", context.header_present)

    if context.school is not None:
        setattr(request, "school_id", str(context.school_id))
        setattr(request, "school", context.school)
        setattr(request, "tenant_school", context.school)

    if context.override_authorized:
        setattr(request, "_crown_school_override_id", context.school_id)

    return context


def get_tenant_school_id(request, *, required: bool = True) -> Optional[UUID]:
    """Return canonical tenant school ID, resolving and binding when absent."""
    context = getattr(request, CANONICAL_TENANT_ATTR, None)
    if context is not None and context.school_id:
        return context.school_id

    existing = getattr(request, TENANT_ATTR, None)
    if existing:
        return existing

    context = bind_tenant_context(request, build_tenant_context(request))
    if required and not context.school_id:
        raise PermissionError("TENANT_REQUIRED")

    return context.school_id
