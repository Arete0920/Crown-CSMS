# backend/crown_api/financial_aid_views.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from django.db.models import Count, Sum, Q, Case, When, Value, IntegerField, CharField, OuterRef, Subquery
from django.utils.timezone import now
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status as drf_status

from aid.models import AidApplication, AidAward


ALLOWED_BUCKETS = {"need", "mission", "merit", "marketing", "hardship"}
ALLOWED_STATUSES = {"submitted", "reviewed", "awarded", "denied"}


def _int_param(request, name: str, default: int, min_v: int, max_v: int) -> int:
    raw = request.query_params.get(name)
    if raw is None or raw == "":
        return default
    try:
        v = int(raw)
    except ValueError:
        return default
    return max(min_v, min(max_v, v))


def _str_param(request, name: str) -> Optional[str]:
    v = request.query_params.get(name)
    if v is None:
        return None
    v = v.strip()
    return v or None


def _normalize_bucket(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    v = v.strip().lower()
    return v if v in ALLOWED_BUCKETS else None


def _normalize_status(v: Optional[str]) -> Optional[str]:
    if not v:
        return None
    v = v.strip().lower()
    return v if v in ALLOWED_STATUSES else None


def _require_school_id(request) -> Optional[str]:
    return request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")


def _map_app_status_to_dashboard(status: str) -> str:
    """Map AidApplication status to dashboard status."""
    mapping = {
        AidApplication.STATUS_SUBMITTED: "submitted",
        AidApplication.STATUS_UNDER_REVIEW: "reviewed",
        AidApplication.STATUS_NEEDS_INFO: "reviewed",
        AidApplication.STATUS_APPROVED: "awarded",
        AidApplication.STATUS_DENIED: "denied",
        AidApplication.STATUS_WITHDRAWN: "denied",
        AidApplication.STATUS_DRAFT: "submitted",  # treat as submitted for dashboard
    }
    return mapping.get(status, "submitted")


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def financial_aid_drilldown(request):
    """
    Drilldown list endpoint for Financial Aid dashboard.
    Tenant-scoped via X-School-Id.
    """
    school_id = _require_school_id(request)
    if not school_id:
        return Response(
            {"detail": "Missing X-School-Id header."},
            status=drf_status.HTTP_400_BAD_REQUEST,
        )

    bucket = _normalize_bucket(_str_param(request, "bucket"))
    status_v = _normalize_status(_str_param(request, "status"))
    q = _str_param(request, "q")

    page = _int_param(request, "page", default=1, min_v=1, max_v=10_000)
    page_size = _int_param(request, "page_size", default=25, min_v=1, max_v=200)
    offset = (page - 1) * page_size
    limit = offset + page_size

    # Base queryset (tenant-scoped AidApplication).
    qs = AidApplication.objects.filter(school_id=school_id).select_related("family")

    # Annotate with latest award info
    latest_award_subquery = AidAward.objects.filter(
        school_id=school_id,
        student__family=OuterRef("family")
    ).order_by("-updated_at").values("awarded_cents", "decision_status", "award_type")[:1]

    qs = qs.annotate(
        awarded_cents=Subquery(latest_award_subquery.values("awarded_cents")[:1], output_field=IntegerField()),
        decision_status=Subquery(latest_award_subquery.values("decision_status")[:1]),
        award_type=Subquery(latest_award_subquery.values("award_type")[:1]),
    )

    # Optional filters
    if bucket:
        qs = qs.filter(Q(award_type__iexact=bucket))  # filter on award type
    if status_v:
        # Map dashboard status back to app statuses
        app_statuses = []
        if status_v == "submitted":
            app_statuses = [AidApplication.STATUS_SUBMITTED, AidApplication.STATUS_DRAFT]
        elif status_v == "reviewed":
            app_statuses = [AidApplication.STATUS_UNDER_REVIEW, AidApplication.STATUS_NEEDS_INFO]
        elif status_v == "awarded":
            app_statuses = [AidApplication.STATUS_APPROVED]
        elif status_v == "denied":
            app_statuses = [AidApplication.STATUS_DENIED, AidApplication.STATUS_WITHDRAWN]
        if app_statuses:
            qs = qs.filter(status__in=app_statuses)
    if q:
        qs = qs.filter(
            Q(family__family_name__icontains=q)
            | Q(family__parent_email__icontains=q)
        )

    # Summary totals
    summary = qs.aggregate(
        count=Count("id"),
        total_awarded=Sum(Case(When(decision_status="ACCEPTED", then="awarded_cents"), default=0, output_field=IntegerField())),
    )
    summary_out = {
        "count": int(summary.get("count") or 0),
        "total_requested": 0,  # placeholder, no requested field
        "total_awarded": int(summary.get("total_awarded") or 0),
    }

    # Facets
    facet_base = AidApplication.objects.filter(school_id=school_id).annotate(
        decision_status=Subquery(latest_award_subquery.values("decision_status")[:1]),
        award_type=Subquery(latest_award_subquery.values("award_type")[:1]),
    )
    if status_v:
        facet_base = facet_base.filter(status__in=app_statuses)
    if q:
        facet_base = facet_base.filter(
            Q(family__family_name__icontains=q)
            | Q(family__parent_email__icontains=q)
        )

    # Bucket facets from awards
    bucket_counts = (
        facet_base.exclude(award_type__isnull=True).values("award_type")
        .annotate(c=Count("id"))
        .order_by()
    )

    # Status facets from app status mapped
    status_mapping = Case(
        When(status__in=[AidApplication.STATUS_SUBMITTED, AidApplication.STATUS_DRAFT], then=Value("submitted")),
        When(status__in=[AidApplication.STATUS_UNDER_REVIEW, AidApplication.STATUS_NEEDS_INFO], then=Value("reviewed")),
        When(status=AidApplication.STATUS_APPROVED, then=Value("awarded")),
        When(status__in=[AidApplication.STATUS_DENIED, AidApplication.STATUS_WITHDRAWN], then=Value("denied")),
        default=Value("submitted"),
        output_field=CharField()
    )
    status_counts = (
        facet_base.annotate(dashboard_status=status_mapping).values("dashboard_status")
        .annotate(c=Count("id"))
        .order_by()
    )

    facets = {
        "bucket": {row["award_type"]: int(row["c"]) for row in bucket_counts if row["award_type"]},
        "status": {row["dashboard_status"]: int(row["c"]) for row in status_counts if row["dashboard_status"]},
    }

    # Items
    rows = (
        qs.order_by("-updated_at")
        .values(
            "id",
            "family__family_name",
            "status",
            "submitted_at",
            "updated_at",
            "awarded_cents",
            "decision_status",
            "award_type",
        )[offset:limit]
    )

    items = []
    for r in rows:
        dashboard_status = _map_app_status_to_dashboard(r.get("status"))
        awarded = int(r.get("awarded_cents") or 0) if r.get("decision_status") == "ACCEPTED" else 0
        items.append(
            {
                "id": str(r["id"]),
                "student_name": r.get("family__family_name") or "",  # placeholder, no student name
                "grade": "",  # placeholder
                "bucket": r.get("award_type") or "need",  # default to need
                "status": dashboard_status,
                "requested": None,  # no requested field
                "awarded": awarded,
                "submitted_at": r.get("submitted_at"),
                "updated_at": r.get("updated_at"),
            }
        )

    return Response(
        {
            "ok": True,
            "filters": {
                "bucket": bucket,
                "status": status_v,
                "q": q,
                "page": page,
                "page_size": page_size,
            },
            "summary": summary_out,
            "facets": facets,
            "items": items,
        }
    )