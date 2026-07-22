import uuid
from typing import Optional

from django.utils import timezone

from crown_api.audit_models import AuditEvent
from crown_api.permissions import _get_user_role


def _coerce_uuid(value) -> Optional[uuid.UUID]:
    try:
        return uuid.UUID(str(value).strip()) if value else None
    except Exception:
        return None


def _get_school_id_from_request(request) -> Optional[uuid.UUID]:
    """Prefer authorized canonical tenant context; fall back for unbound requests."""
    context = getattr(request, "crown_tenant", None)
    if context is not None:
        return _coerce_uuid(getattr(context, "school_id", None))

    tenant_school_id = _coerce_uuid(getattr(request, "tenant_school_id", None))
    if tenant_school_id:
        return tenant_school_id

    hdr = None
    try:
        hdr = request.headers.get("X-School-Id")
    except Exception:
        hdr = None
    if not hdr:
        hdr = request.META.get("HTTP_X_SCHOOL_ID")
    return _coerce_uuid(hdr)


def _get_correlation_id(request) -> str:
    existing = getattr(request, "crown_correlation_id", None)
    if existing:
        return str(existing)

    headers = getattr(request, "headers", {})
    correlation_id = (
        headers.get("X-Correlation-Id")
        or headers.get("X-Request-Id")
        or request.META.get("HTTP_X_CORRELATION_ID")
        or request.META.get("HTTP_X_REQUEST_ID")
        or str(uuid.uuid4())
    )
    setattr(request, "crown_correlation_id", str(correlation_id))
    return str(correlation_id)


def tenant_decision_meta(request, *, outcome: str, reason: Optional[str] = None) -> dict:
    """Return normalized, non-secret tenant-decision evidence for audit persistence."""
    context = getattr(request, "crown_tenant", None)
    return {
        "actor_type": getattr(context, "actor_type", "unknown"),
        "principal_school_id": str(getattr(context, "principal_school_id", "") or ""),
        "selected_school_id": str(getattr(context, "school_id", "") or ""),
        "source": getattr(context, "source", "unbound"),
        "header_present": bool(getattr(context, "header_present", False)),
        "override_requested": bool(getattr(context, "override_requested", False)),
        "override_authorized": bool(getattr(context, "override_authorized", False)),
        "outcome": str(outcome).strip(),
        "reason": str(reason).strip() if reason else None,
        "route": str(getattr(request, "path", "") or ""),
        "method": str(getattr(request, "method", "") or ""),
        "correlation_id": _get_correlation_id(request),
    }


def audit_log(
    *,
    request,
    action: str,
    object_type: Optional[str] = None,
    object_id: Optional[uuid.UUID] = None,
    meta: Optional[dict] = None,
) -> AuditEvent:
    """
    Minimal audit helper. Safe defaults. No secrets in meta.
    """
    user = getattr(request, "user", None)
    actor_id = _coerce_uuid(getattr(user, "id", None))

    evt = AuditEvent.objects.create(
        ts=timezone.now(),
        school_id=_get_school_id_from_request(request),
        actor_id=actor_id,
        actor_role=_get_user_role(request),
        action=str(action).strip(),
        object_type=str(object_type).strip() if object_type else None,
        object_id=object_id,
        meta=meta or {},
    )
    return evt


def audit_tenant_decision(request, *, outcome: str, reason: Optional[str] = None) -> AuditEvent:
    """Persist a structured tenant authorization decision."""
    return audit_log(
        request=request,
        action="tenant.context.decision",
        object_type="tenant_context",
        object_id=_get_school_id_from_request(request),
        meta=tenant_decision_meta(request, outcome=outcome, reason=reason),
    )
