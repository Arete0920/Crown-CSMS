# backend/crown_api/audit_views.py
from uuid import UUID

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from crown_api.audit_models import AuditEvent
from crown_api.permissions import require_roles
from crown_api.request_parsing import parse_bounded_int


@require_GET
@require_roles(["admin", "finance"])
def recent_audit_events(request):
    """
    Proof endpoint: returns the most recent audit events.
    Demo-safe; does not create new events.
    """
    limit = parse_bounded_int(
        request.GET.get("limit", "25"),
        default=25,
        min_value=1,
        max_value=100,
    )

    qs = AuditEvent.objects.order_by("-ts")

    # Tenant filter: scope to school when X-School-Id header is provided.
    # This prevents cross-tenant audit event leakage for school-scoped callers.
    raw_sid = request.META.get("HTTP_X_SCHOOL_ID") or request.headers.get("X-School-Id")
    if raw_sid:
        try:
            school_uuid = UUID(str(raw_sid))
        except Exception:
            return JsonResponse({"ok": False, "error": "invalid X-School-Id header"}, status=400)
        qs = qs.filter(school_id=school_uuid)

    qs = qs[:limit]

    rows = []
    for e in qs:
        rows.append(
            {
                "id": str(e.id),
                "ts": e.ts.isoformat(),
                "school_id": str(e.school_id) if e.school_id else None,
                "actor_id": str(e.actor_id) if e.actor_id else None,
                "actor_role": e.actor_role,
                "action": e.action,
                "object_type": e.object_type,
                "object_id": str(e.object_id) if e.object_id else None,
                "meta": e.meta or {},
            }
        )

    return JsonResponse({"ok": True, "count": len(rows), "results": rows})
