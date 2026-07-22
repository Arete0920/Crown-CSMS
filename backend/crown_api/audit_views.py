# backend/crown_api/audit_views.py
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from crown_api.audit_models import AuditEvent
from crown_api.permissions import require_roles
from crown_api.request_parsing import parse_bounded_int
from crown_api.tenant import CANONICAL_TENANT_ATTR, build_tenant_context


@require_GET
@require_roles(["admin", "finance"])
def recent_audit_events(request):
    """Return recent audit events for the caller's authorized tenant only."""
    limit = parse_bounded_int(
        request.GET.get("limit", "25"),
        default=25,
        min_value=1,
        max_value=100,
    )

    context = getattr(request, CANONICAL_TENANT_ATTR, None)
    if context is None:
        context = build_tenant_context(request)

    if not context.school_id:
        return JsonResponse(
            {"ok": False, "error": "Tenant context required"},
            status=403,
        )

    if context.override_requested and not context.override_authorized:
        return JsonResponse(
            {"ok": False, "error": "Not found"},
            status=404,
        )

    queryset = AuditEvent.objects.filter(school_id=context.school_id).order_by("-ts")[:limit]

    rows = []
    for event in queryset:
        rows.append(
            {
                "id": str(event.id),
                "ts": event.ts.isoformat(),
                "school_id": str(event.school_id) if event.school_id else None,
                "actor_id": str(event.actor_id) if event.actor_id else None,
                "actor_role": event.actor_role,
                "action": event.action,
                "object_type": event.object_type,
                "object_id": str(event.object_id) if event.object_id else None,
                "meta": event.meta or {},
            }
        )

    return JsonResponse({"ok": True, "count": len(rows), "results": rows})
