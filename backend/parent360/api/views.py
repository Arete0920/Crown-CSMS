from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


# ---------------------------------------------------------------------------
# Helpers  (mirrors student360 helpers so behaviour is consistent)
# ---------------------------------------------------------------------------

def _safe_decimal(x, default=Decimal("0")):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _compute_weighted_percent(grade_qs):
    earned = Decimal("0")
    possible = Decimal("0")
    for ge in grade_qs:
        pe = _safe_decimal(getattr(ge, "points_earned", None))
        pp = _safe_decimal(getattr(ge, "points_possible", None))
        if pp > 0:
            possible += pp
            earned += pe
    if possible <= 0:
        return None
    return (earned / possible) * Decimal("100")


def _percent_to_gpa_proxy(pct):
    if pct is None:
        return None
    for threshold, gpa in [
        (93, "4.0"), (90, "3.7"), (87, "3.3"), (83, "3.0"),
        (80, "2.7"), (77, "2.3"), (73, "2.0"), (70, "1.7"),
        (67, "1.3"), (65, "1.0"),
    ]:
        if pct >= threshold:
            return Decimal(gpa)
    return Decimal("0.0")


def _try_get_core_student(households_student):
    """Bridge households.Student → core.Student for ServiceEntry FK (legacy)."""
    try:
        from core.models import Student as CoreStudent
    except Exception:
        return None

    first = getattr(households_student, "first_name", None)
    last = getattr(households_student, "last_name", None)
    if first and last:
        cs = CoreStudent.objects.filter(
            first_name__iexact=first, last_name__iexact=last
        ).first()
        if cs:
            return cs
    return None


def _resolve_household_for_user(user):
    """
    Resolve the calling user to a households.Household.

    Primary: match user.email → households.Guardian.email (Guardian has household FK).
    Demo-safe; not production-safe without a direct User ↔ Household FK.
    """
    email = getattr(user, "email", None)
    if not email:
        return None

    try:
        from households.models import Guardian
        guardian = (
            Guardian.objects.filter(email__iexact=email)
            .select_related("household")
            .first()
        )
        if guardian and getattr(guardian, "household_id", None):
            return guardian.household
    except Exception:
        logger.debug("guardian email bridge unavailable", exc_info=True)

    return None


def _get_children_for_household(household):
    """Return list of active households.Student for the household."""
    try:
        from households.models import Student as HHStudent
    except Exception:
        return []
    try:
        qs = HHStudent.objects.filter(household=household)
        if hasattr(HHStudent, "is_active"):
            qs = qs.filter(is_active=True)
        return list(qs.order_by("last_name", "first_name"))
    except Exception:
        return []


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class ParentSelfOverview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        household = _resolve_household_for_user(user)
        if not household:
            return Response(
                {
                    "detail": (
                        "No household found for current user. "
                        "(Demo bridge: Guardian email match failed — contact school admin.)"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        children = _get_children_for_household(household)

        # Optional model imports — degrade gracefully if any app is missing.
        GradeEntry = None
        Assignment = None
        Invoice = None
        InvoiceLine = None
        ServiceEntry = None

        try:
            from gradebook.models import GradeEntry
            from academics.models import Assignment
        except Exception:
            logger.debug("gradebook/academics optional imports unavailable", exc_info=True)

        try:
            from billing.models import Invoice, InvoiceLine
        except Exception:
            logger.debug("billing optional imports unavailable", exc_info=True)

        try:
            from servicehours.models import ServiceEntry
        except Exception:
            logger.debug("servicehours optional imports unavailable", exc_info=True)

        now = timezone.now().date()
        seven_days = now + timezone.timedelta(days=7)

        # ── Household balance (open invoices, if Invoice is household-scoped) ──
        household_balance_cents = 0
        if Invoice is not None and hasattr(Invoice, "household"):
            try:
                inv_qs = Invoice.objects.filter(household=household)
                if hasattr(Invoice, "status"):
                    inv_qs = inv_qs.filter(status__in=["open", "unpaid", "pending"])
                elif hasattr(Invoice, "is_paid"):
                    inv_qs = inv_qs.filter(is_paid=False)

                if InvoiceLine is not None and hasattr(InvoiceLine, "invoice"):
                    lines_total = InvoiceLine.objects.filter(invoice__in=inv_qs).aggregate(
                        total=Coalesce(Sum("amount"), Decimal("0"))
                    )["total"]
                    household_balance_cents = int(
                        (_safe_decimal(lines_total) * Decimal("100")).quantize(Decimal("1"))
                    )
                elif hasattr(Invoice, "amount_due"):
                    raw = inv_qs.aggregate(total=Coalesce(Sum("amount_due"), Decimal("0")))["total"]
                    household_balance_cents = int(
                        (_safe_decimal(raw) * Decimal("100")).quantize(Decimal("1"))
                    )
            except Exception:
                logger.debug("household balance unavailable", exc_info=True)

        # ── Per-child blocks ──────────────────────────────────────────────────
        child_rows = []
        missing_total = 0
        upcoming_total = 0

        for s in children:
            school_id = getattr(s, "school_id", None)

            row = {
                "id": str(getattr(s, "id")),
                "first_name": getattr(s, "first_name", ""),
                "last_name": getattr(s, "last_name", ""),
                "grade_level": getattr(s, "grade_level", ""),
                "current_average": None,
                "gpa": None,
                "missing_assignments": 0,
                "upcoming_assignments": [],
                "service_hours": {"available": False, "completed": 0, "required": 30},
                "financial": {"available": False, "balance_cents": 0},
                "alerts": [],
            }

            # ── Grades ──────────────────────────────────────────────────────
            if GradeEntry is not None and Assignment is not None:
                try:
                    ge_qs = GradeEntry.objects.filter(student=s).select_related("assignment")
                    pct = _compute_weighted_percent(ge_qs)
                    if pct is not None:
                        row["current_average"] = float(pct.quantize(Decimal("0.1")))
                        gpa = _percent_to_gpa_proxy(pct)
                        row["gpa"] = float(gpa) if gpa is not None else None

                    # Missing assignments: published + past-due + no entry or blank entry
                    asgn_filter = {"is_published": True, "due_date__lt": now}
                    if school_id:
                        asgn_filter["school_id"] = school_id

                    past_due_qs = Assignment.objects.filter(**asgn_filter)
                    entered_ids = set(
                        ge_qs.exclude(assignment=None).values_list("assignment_id", flat=True)
                    )

                    missing_no_entry = past_due_qs.exclude(id__in=entered_ids).count()
                    missing_blank = ge_qs.filter(
                        assignment__is_published=True,
                        assignment__due_date__lt=now,
                    ).filter(
                        Q(points_earned__isnull=True) | Q(points_possible__isnull=True)
                    ).count()

                    row["missing_assignments"] = int(missing_no_entry + missing_blank)

                    # Upcoming assignments: next 7 days
                    up_filter = {"is_published": True, "due_date__gte": now, "due_date__lte": seven_days}
                    if school_id:
                        up_filter["school_id"] = school_id

                    upcoming = list(
                        Assignment.objects.filter(**up_filter).order_by("due_date")[:3]
                    )
                    row["upcoming_assignments"] = [
                        {
                            "id": str(a.id),
                            "name": a.name,
                            "due_date": a.due_date.isoformat() if a.due_date else None,
                            "points_possible": (
                                float(_safe_decimal(a.points_possible))
                                if a.points_possible is not None else None
                            ),
                        }
                        for a in upcoming
                    ]

                    missing_total += row["missing_assignments"]
                    upcoming_total += len(row["upcoming_assignments"])
                except Exception:
                    logger.debug("optional assignment data unavailable for child", exc_info=True)

            # ── Service hours ──────────────────────────────────────────────
            if ServiceEntry is not None:
                try:
                    core_student = _try_get_core_student(s)
                    if core_student:
                        approved = ServiceEntry.objects.filter(
                            student=core_student, status="approved"
                        )
                        total_h = approved.aggregate(
                            total=Coalesce(Sum("hours"), Decimal("0"))
                        )["total"]
                        row["service_hours"] = {
                            "available": True,
                            "completed": float(_safe_decimal(total_h).quantize(Decimal("0.1"))),
                            "required": 30,
                        }
                except Exception:
                    logger.debug("optional service hours unavailable for child", exc_info=True)

            # ── Finance per student (InvoiceLine.student FK) ────────────────
            if InvoiceLine is not None and Invoice is not None:
                try:
                    lines = InvoiceLine.objects.filter(student=s).select_related("invoice")

                    inv_filter = Q()
                    if hasattr(Invoice, "status"):
                        inv_filter = Q(invoice__status__in=["open", "unpaid", "pending"])
                    elif hasattr(Invoice, "is_paid"):
                        inv_filter = Q(invoice__is_paid=False)

                    if inv_filter:
                        lines = lines.filter(inv_filter)

                    total_amount = lines.aggregate(
                        total=Coalesce(Sum("amount"), Decimal("0"))
                    )["total"]
                    row["financial"] = {
                        "available": True,
                        "balance_cents": int(
                            (_safe_decimal(total_amount) * Decimal("100")).quantize(Decimal("1"))
                        ),
                    }
                except Exception:
                    logger.debug("optional finance data unavailable for child", exc_info=True)

            # ── Alerts ──────────────────────────────────────────────────────
            if row["current_average"] is not None and row["current_average"] < 75:
                row["alerts"].append({
                    "type": "academic",
                    "severity": "warning",
                    "message": f"{row['first_name']} has an average below 75%.",
                })
            if row["missing_assignments"] >= 3:
                row["alerts"].append({
                    "type": "work",
                    "severity": "warning",
                    "message": f"{row['first_name']} has 3+ missing assignments.",
                })

            child_rows.append(row)

        payload = {
            "household": {
                "id": str(getattr(household, "id")),
                "name": getattr(household, "name", ""),
                "balance_cents": household_balance_cents,
            },
            "children_count": len(child_rows),
            "missing_assignments_total": missing_total,
            "upcoming_assignments_total": upcoming_total,
            "children": child_rows,
        }

        return Response(payload, status=status.HTTP_200_OK)
