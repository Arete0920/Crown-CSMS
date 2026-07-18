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

from crown_api.tenant import get_tenant_school_id
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_entitlements(request) -> Response:
    """Return an entitlement snapshot for the canonical current tenant."""
    try:
        school_id = get_tenant_school_id(request, required=True)
    except PermissionError:
        return Response({"error": "X-School-ID header is required."}, status=400)

    try:
        sub = EntitlementsService.get_active_subscription(school_id)
    except TenantSubscription.DoesNotExist:
        return Response({"error": "No active subscription found for this school."}, status=404)

    features = Feature.objects.order_by("key")
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def plan_list(request) -> Response:
    """List all active plans with entitlements."""
    plans = Plan.objects.filter(is_active=True).prefetch_related(
        "entitlements", "entitlements__feature"
    )
    serializer = PlanSerializer(plans, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def feature_list(request) -> Response:
    """List all registered feature keys."""
    features = Feature.objects.order_by("key")
    serializer = FeatureSerializer(features, many=True)
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAdminUser])
def ops_school_subscription(request, school_id: uuid.UUID) -> Response:
    """Read or update a school's active subscription as an administrator."""
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

    data = request.data
    plan_id = data.get("plan_id")
    is_trial = bool(data.get("is_trial", False))

    if not plan_id:
        return Response({"error": "plan_id is required."}, status=400)

    try:
        plan = Plan.objects.get(pk=plan_id)
    except Plan.DoesNotExist:
        return Response({"error": f"Plan {plan_id} not found."}, status=404)

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
