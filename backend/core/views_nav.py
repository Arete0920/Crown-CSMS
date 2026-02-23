# backend/core/views_nav.py
#
# GET /api/v1/nav/
#
# Returns the left-sidebar nav items filtered by backend-authoritative
# permission checks.  TenantHeaderRequiredMiddleware must run first — it
# validates X-School-Id and sets request.school.  This view never needs to
# touch the header itself.

from collections import defaultdict

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from core.nav_registry import NAV_ITEMS
from core.permissions import user_has_permission


@require_http_methods(["GET"])
def nav_view(request):
    """
    Returns grouped nav items the authenticated user is permitted to see.

    Response shape:
      {
        "groups": [
          { "title": "Operations", "items": [{"label": "Finance", "href": "/finance"}, ...] },
          ...
        ]
      }

    Empty groups are omitted.  Group order matches NAV_ITEMS declaration order.
    """
    school = getattr(request, "school", None)
    # Middleware already rejects requests missing X-School-Id with 400.
    # This is a belt-and-suspenders guard for any non-/api/v1/ usage.
    if school is None:
        return JsonResponse(
            {"detail": "Missing tenant context (X-School-Id required)."},
            status=400,
        )

    grouped: dict[str, list] = defaultdict(list)

    for item in NAV_ITEMS:
        if item.permission is None:
            allowed = True
        else:
            allowed = user_has_permission(request.user, item.permission, school=school)

        if allowed:
            grouped[item.group].append(
                {"label": item.label, "href": item.href}
            )

    # Preserve declaration order for groups
    group_order: list[str] = []
    for item in NAV_ITEMS:
        if item.group not in group_order:
            group_order.append(item.group)

    return JsonResponse(
        {
            "groups": [
                {"title": g, "items": grouped[g]}
                for g in group_order
                if grouped.get(g)
            ]
        },
        status=200,
    )
