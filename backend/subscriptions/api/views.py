"""
Subscriptions API views.

Routes:
  GET  /api/v1/subscriptions/me/entitlements/    — current tenant's full entitlement snapshot
  GET  /api/v1/subscriptions/plans/              — list all active plans (public/authenticated)
  GET  /api/v1/subscriptions/features/           — list all feature keys (public/authenticated)
  GET  /api/v1/subscriptions/ops/<school_id>/    — ops: get subscription for any school [IsAdminUser]
  POST /api/v1/subscriptions/ops/<school_id>/    — ops: assign/update plan for a school [IsAdminUser]
"""
from __future__ import annotations

import uuid

from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from subscriptions.models import (
    EntitlementOverride,
    Feature,
    Plan,
    PlanEntitlement,
    TenantSubscription,
)
from subscriptions.services import EntitlementsService

from .serializers import (
    FeatureSerializer,
    PlanListSerializer,
    PlanSerializer,
    TenantSubscriptionSerializer,
)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/subscriptions/me/entitlements/
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_entitlements(request) -> Response:
    """
    Return an entitlement snapshot for the current tenant (from X-School-ID header).

    Shape:
      {
        "plan_code": "smart_start",
        "plan_name": "Smart Start",
        "is_trial": false,
        "entitlements": {
          "admissions.pipeline": {"enabled": true, "limit_int": null, "used_int": null},
          ...
        }
      }
    """
    school_id = getattr(request, "school_id", None)
    if not school_id:
        return Response({"error": "X-School-ID header is required."}, status=400)

    try:
        sub = EntitlementsService.get_active_subscription(school_id)
    except TenantSubscription.DoesNotExist:
        return Response({"error": "No active subscription found for this school."}, status=404)

    # Build full entitlement map from plan + overrides + usage counters
    features = Feature.objects.all()
    entitlements: dict[str, dict] = {}
    for feature in features:
        try:
            ent = EntitlementsService.get_entitlement(school_id, feature.key)
            entitlements[feature.key] = {
                "enabled": ent.enabled,
                "limit_int": ent.limit_int,
                "used_int": ent.used_int,
            }
        except Exception:
            entitlements[feature.key] = {"enabled": False, "limit_int": None, "used_int": None}

    return Response(
        {
            "plan_code": sub.plan.code,
            "plan_name": sub.plan.name,
            "is_trial": sub.is_trial,
            "entitlements": entitlements,
        }
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/subscriptions/plans/
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plan_list(request) -> Response:
    """List all active plans with entitlements."""
    plans = Plan.objects.filter(is_active=True).prefetch_related(
        "entitlements", "entitlements__feature"
    )
    serializer = PlanSerializer(plans, many=True)
    return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/subscriptions/features/
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feature_list(request) -> Response:
    """List all registered feature keys."""
    features = Feature.objects.all()
    serializer = FeatureSerializer(features, many=True)
    return Response(serializer.data)


# ─────────────────────────────────────────────────────────────────────────────
# GET + POST /api/v1/subscriptions/ops/<school_id>/
# ─────────────────────────────────────────────────────────────────────────────

@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def ops_school_subscription(request, school_id: uuid.UUID) -> Response:
    """
    Super-admin endpoint: read or update a school's active subscription.

    GET  — returns current TenantSubscription (404 if none)
    POST — body: {"plan_id": <int>, "is_trial": <bool>}
           Creates subscription if none exists; updates plan/is_trial if one exists.
           A new subscription always starts now with ended_at=null.
    """
    if request.method == "GET":
        try:
            sub = TenantSubscription.objects.select_related("plan").get(
                school_id=school_id, ended_at__isnull=True
            )
        except TenantSubscription.DoesNotExist:
            return Response(
                {"error": f"No active subscription for school {school_id}."}, status=404
            )
        serializer = TenantSubscriptionSerializer(sub)
        return Response(serializer.data)

    # POST — assign or change plan
    data = request.data
    plan_id = data.get("plan_id")
    is_trial = bool(data.get("is_trial", False))

    if not plan_id:
        return Response({"error": "plan_id is required."}, status=400)

    try:
        plan = Plan.objects.get(pk=plan_id)
    except Plan.DoesNotExist:
        return Response({"error": f"Plan {plan_id} not found."}, status=404)

    # Close existing active subscription (end-date it) and create new one
    TenantSubscription.objects.filter(
        school_id=school_id, ended_at__isnull=True
    ).update(ended_at=timezone.now())

    sub = TenantSubscription.objects.create(
        school_id=school_id,
        plan=plan,
        is_trial=is_trial,
        started_at=timezone.now(),
    )

    serializer = TenantSubscriptionSerializer(sub)
    return Response(serializer.data, status=201)
