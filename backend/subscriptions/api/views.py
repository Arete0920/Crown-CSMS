"""
Subscriptions API views.

Routes:
  GET  /api/v1/subscriptions/me/entitlements/    — current tenant's full entitlement snapshot
  GET  /api/v1/subscriptions/plans/              — list all active plans (public/authenticated)
  GET  /api/v1/subscriptions/features/           — list all feature keys (public/authenticated)
  GET  /api/v1/subscriptions/ops/<school_id>/    — ops: get subscription for any school [IsPlatformOperator]
  POST /api/v1/subscriptions/ops/<school_id>/    — ops: assign/update plan for a school [IsPlatformOperator]
"""
from __future__ import annotations

import uuid

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from core.models import School
from core.permissions import IsPlatformOperator
from platform_ops.models import AuditEvent
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
@permission_classes([IsPlatformOperator])
def ops_school_subscription(request, school_id: uuid.UUID) -> Response:
    """Read or change one existing school's plan with a durable audit trail.

    The feature-entitlement plan is not a CROWN corporate revenue ledger.
    Writes lock the school identity, validate the input and active plan, and
    commit subscription history with an audit event in the same transaction.
    A repeated request for the existing plan/trial state is a no-op.
    """
    if request.method == "GET":
        if not School.objects.filter(pk=school_id).exists():
            return Response({"error": "School not found."}, status=404)

        current = list(
            TenantSubscription.objects.select_related("plan")
            .filter(school_id=school_id, ended_at__isnull=True)
            .order_by("-started_at", "-pk")[:2]
        )
        if len(current) > 1:
            return Response(
                {"error": "Multiple active subscriptions require operator review."},
                status=409,
            )
        if not current:
            return Response(
                {"error": "No active subscription for this school."},
                status=404,
            )
        return Response(TenantSubscriptionSerializer(current[0]).data)

    raw_plan_id = request.data.get("plan_id")
    try:
        if (
            isinstance(raw_plan_id, bool)
            or not isinstance(raw_plan_id, (str, int))
            or len(str(raw_plan_id)) > 18
        ):
            raise ValueError("Invalid plan identifier.")
        plan_id = int(raw_plan_id)
        if plan_id < 1:
            raise ValueError("Invalid plan identifier.")
    except (TypeError, ValueError):
        return Response(
            {"error": "plan_id must be a positive integer."}, status=400
        )

    is_trial = request.data.get("is_trial", False)
    if not isinstance(is_trial, bool):
        return Response(
            {"error": "is_trial must be a JSON boolean."}, status=400
        )

    with transaction.atomic():
        # A school-level lock serializes competing assignments, including
        # the initial assignment when no subscription row exists to lock.
        school = School.objects.select_for_update().filter(pk=school_id).first()
        if school is None:
            return Response({"error": "School not found."}, status=404)

        plan = Plan.objects.filter(pk=plan_id, is_active=True).first()
        if plan is None:
            return Response(
                {"error": "Active plan not found."}, status=404
            )

        existing = list(
            TenantSubscription.objects.select_for_update()
            .select_related("plan")
            .filter(school_id=school_id, ended_at__isnull=True)
            .order_by("-started_at", "-pk")[:2]
        )
        if len(existing) > 1:
            return Response(
                {"error": "Multiple active subscriptions require operator review."},
                status=409,
            )

        previous = existing[0] if existing else None
        if previous and previous.plan_id == plan.id and previous.is_trial == is_trial:
            return Response(TenantSubscriptionSerializer(previous).data, status=200)

        changed_at = timezone.now()
        if previous:
            TenantSubscription.objects.filter(
                pk=previous.pk, ended_at__isnull=True
            ).update(ended_at=changed_at)

        subscription = TenantSubscription.objects.create(
            school_id=school.id,
            plan=plan,
            is_trial=is_trial,
            started_at=changed_at,
        )

        # Never silently accept a plan change that could not be audited.
        # Audit persistence participates in the same atomic transaction.
        AuditEvent.objects.create(
            school_id=school.id,
            actor_user_id=request.user.pk,
            action="subscription.plan_changed" if previous else "subscription.plan_assigned",
            resource_kind="School",
            resource_id=school.id,
            payload={
                "previous_plan": previous.plan.code if previous else None,
                "new_plan": plan.code,
                "previous_trial": previous.is_trial if previous else None,
                "new_trial": is_trial,
            },
        )

    return Response(TenantSubscriptionSerializer(subscription).data, status=201)
