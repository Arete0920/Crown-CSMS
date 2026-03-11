from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db.models import F, Sum
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import permissions
from rest_framework.views import APIView

from core.models import School


def _get_school(request):
    school = getattr(request, "school", None)
    if school:
        return school
    sid = request.headers.get("X-School-Id")
    if not sid:
        return None
    try:
        return School.objects.get(pk=sid)
    except School.DoesNotExist:
        return None


class ExecutiveSelfOverview(APIView):
    """
    GET /api/executive360/me/overview/

    School-wide financial, academic-risk, and workload snapshot for administrators.
    All data blocks are guarded — never raises; returns available=false when school
    cannot be resolved or any model is absent.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)

        payload = {
            "available": school is not None,
            "receivables_cents": None,
            "aid_allocated_cents": None,
            "at_risk_count": None,
            "missing_assignments_total": None,
            "upcoming_assignments_7d": None,
            "alerts": [],
        }

        if not school:
            return JsonResponse(payload)

        # ── Receivables: total InvoiceLine.amount across school ────────────
        try:
            from billing.models import InvoiceLine

            total_amount = InvoiceLine.objects.filter(school_id=school.id).aggregate(
                total=Coalesce(Sum("amount"), Decimal("0.00"))
            )["total"]
            payload["receivables_cents"] = int(total_amount * 100)
        except Exception:
            pass

        # ── Aid allocated: sum AidAward.awarded_cents for this school ──────
        try:
            from aid.models import AidAward

            total_aid = AidAward.objects.filter(school=school).aggregate(
                total=Coalesce(Sum("awarded_cents"), 0)
            )["total"]
            payload["aid_allocated_cents"] = int(total_aid)
        except Exception:
            pass

        # ── Academic at-risk: distinct students with any graded entry < 75% ─
        try:
            from gradebook.models import GradeEntry

            at_risk_count = (
                GradeEntry.objects.filter(
                    school_id=school.id,
                    points_possible__gt=0,
                    points_earned__isnull=False,
                    points_earned__lt=F("points_possible") * Decimal("0.75"),
                )
                .values("student_id")
                .distinct()
                .count()
            )
            payload["at_risk_count"] = at_risk_count
        except Exception:
            pass

        # ── Assignment counts ────────────────────────────────────────────────
        try:
            from academics.models import Assignment

            today = timezone.now().date()
            week_end = today + timedelta(days=7)

            payload["missing_assignments_total"] = Assignment.objects.filter(
                school_id=school.id,
                is_published=True,
                due_date__lt=today,
            ).count()

            payload["upcoming_assignments_7d"] = Assignment.objects.filter(
                school_id=school.id,
                is_published=True,
                due_date__gte=today,
                due_date__lte=week_end,
            ).count()
        except Exception:
            pass

        # ── Build alerts ─────────────────────────────────────────────────────
        alerts = []
        at_risk = payload["at_risk_count"]
        if at_risk is not None and at_risk > 0:
            alerts.append(
                {
                    "type": "academic_risk",
                    "label": f"{at_risk} student{'s' if at_risk != 1 else ''} below 75%",
                    "severity": "critical" if at_risk > 10 else "warning",
                }
            )
        missing = payload["missing_assignments_total"]
        if missing is not None and missing > 0:
            alerts.append(
                {
                    "type": "missing_work",
                    "label": f"{missing} overdue assignment{'s' if missing != 1 else ''} school-wide",
                    "severity": "info",
                }
            )
        payload["alerts"] = alerts

        return JsonResponse(payload)
