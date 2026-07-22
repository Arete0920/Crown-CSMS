from __future__ import annotations

import uuid

from rest_framework.exceptions import NotFound, ValidationError

from crown_api.tenant import CANONICAL_TENANT_ATTR, bind_tenant_context, build_tenant_context
from households.scoping import CANONICAL_SCHOOL_HEADER


def _canonical_context(request):
    context = getattr(request, CANONICAL_TENANT_ATTR, None)
    if context is None:
        context = bind_tenant_context(request, build_tenant_context(request))
    return context


def get_dashboard_school_id(request, *, required: bool = True) -> uuid.UUID | None:
    """Resolve dashboard scope through the canonical tenant contract.

    Dashboards intentionally require an explicit tenant header even when the
    authenticated principal has a school fallback. Authorization still comes
    from ``request.crown_tenant`` rather than raw-header or staff heuristics.
    """
    context = _canonical_context(request)

    if context.source == "header_invalid":
        raise ValidationError({"school_id": ["Invalid school_id UUID."]})

    if not context.header_present:
        if required:
            raise ValidationError(
                {
                    "school_id": [
                        f"Missing {CANONICAL_SCHOOL_HEADER} header (tenant context required)."
                    ]
                }
            )
        return None

    school_id = context.school_id
    if not school_id:
        if required:
            raise ValidationError({"school_id": ["Missing school tenant context."]})
        return None

    if context.override_requested and not context.override_authorized:
        raise NotFound({"detail": "Not found"})

    try:
        from core.models import School

        if not School.objects.filter(pk=school_id, is_active=True).exists():
            raise NotFound({"detail": "School not found"})
    except NotFound:
        raise
    except Exception as exc:
        raise NotFound({"detail": "School not found"}) from exc

    return school_id
