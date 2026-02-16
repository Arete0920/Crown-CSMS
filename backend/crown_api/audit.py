# backend/crown_api/audit.py
import uuid
from typing import Optional

from django.utils import timezone

from crown_api.audit_models import AuditEvent
from crown_api.permissions import _get_user_role


def _get_school_id_from_request(request) -> Optional[uuid.UUID]:
    hdr = None
    try:
        hdr = request.headers.get("X-School-Id")
    except Exception:
        hdr = None
    if not hdr:
        hdr = request.META.get("HTTP_X_SCHOOL_ID")
    if not hdr:
        return None
    try:
        return uuid.UUID(str(hdr).strip())
    except Exception:
        return None


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
    actor_id = getattr(user, "id", None)
    try:
        actor_id = uuid.UUID(str(actor_id)) if actor_id else None
    except Exception:
        actor_id = None

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
