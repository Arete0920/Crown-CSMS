from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.http import Http404, JsonResponse
from django.utils import timezone
from drf_spectacular.openapi import AutoSchema as SpectacularAutoSchema
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers
from rest_framework.views import APIView

from core.models import School
from crown_api.access_households import resolve_household_access
from crown_api.scoping_students import get_core_student_or_404_for_request

logger = logging.getLogger(__name__)


def _scope_qs_to_school(qs, model, school):
    """
    Fail-closed tenant scoping helper.
    Every model used in student360 must have either school_id or school.
    Raises ImproperlyConfigured if neither is present — fail loud, not silent.
    """
    if hasattr(model, "school_id"):
        return qs.filter(school_id=str(school.id))
    if hasattr(model, "school"):
        return qs.filter(school=school)
    raise ImproperlyConfigured(
        f"{getattr(model, '__name__', str(model))} must have school_id or school "
        f"for tenant scoping in student360"
    )


class Student360StudentSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    grade = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class Student360OverviewResponseSerializer(serializers.Serializer):
    student = Student360StudentSerializer()
    attendance = serializers.JSONField()
    finance = serializers.JSONField()
    discipline = serializers.JSONField()
    service_hours = serializers.JSONField()
    leadership = serializers.JSONField()
    mentorship = serializers.JSONField()
    comms = serializers.JSONField()
    dashboard_v2 = serializers.JSONField()


# Optional imports (only used if present)
try:
    from crown_api.models_academics_core import AttendanceRecord
except Exception:
    try:
        from attendance.models import AttendanceRecord
    except Exception:
        AttendanceRecord = None

try:
    from discipline.models import DisciplineIncident
except Exception:
    DisciplineIncident = None

try:
    from servicehours.models import ServiceEntry
except Exception:
    ServiceEntry = None

try:
    from crown_api.models_comms_core import MessageThread
except Exception:
    MessageThread = None


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


def _get_household_student_model():
    try:
        from households.models import Student as HouseholdStudent

        return HouseholdStudent
    except Exception:
        logger.debug("households.Student unavailable", exc_info=True)
        return None


def _get_core_student_model():
    try:
        from core.models import Student as CoreStudent

        return CoreStudent
    except Exception:
        logger.debug("core.Student unavailable", exc_info=True)
        return None


def _find_student_model():
    return _get_household_student_model() or _get_core_student_model()


def _query_student_by_id(model, school, student_id):
    if model is None:
        return None
    try:
        qs = _scope_qs_to_school(model.objects.all(), model, school)
        return qs.filter(pk=student_id).first()
    except Exception:
        logger.debug("student lookup failed", exc_info=True)
        return None


def _student_name(student) -> str:
    if not student:
        return "Unknown Student"
    full_name = getattr(student, "full_name", None)
    if callable(full_name):
        full_name = full_name()
    if full_name:
        return str(full_name)
    first = (getattr(student, "first_name", "") or "").strip()
    last = (getattr(student, "last_name", "") or "").strip()
    return f"{first} {last}".strip() or "Unknown Student"


def _student_grade(student):
    if not student:
        return None
    grade = getattr(student, "grade_level", None)
    if grade not in (None, ""):
        return grade
    current_grade = getattr(student, "current_grade_level", None)
    return getattr(current_grade, "code", None) or getattr(current_grade, "label", None)


def _try_get_core_student(households_student, *, school=None):
    """Bridge households.Student → core.Student for service/attendance/discipline models."""
    core_student_model = _get_core_student_model()
    if core_student_model is None or households_student is None:
        return None

    qs = core_student_model.objects.all()
    if school is not None:
        qs = _scope_qs_to_school(qs, core_student_model, school)

    email = getattr(households_student, "email", None)
    if email and hasattr(core_student_model, "email"):
        cs = qs.filter(email__iexact=email).first()
        if cs:
            return cs

    first = getattr(households_student, "first_name", None)
    last = getattr(households_student, "last_name", None)
    if first and last:
        cs = qs.filter(first_name__iexact=first, last_name__iexact=last).first()
        if cs:
            return cs
    return None


def _try_get_household_student(core_student, *, school=None):
    """Bridge core.Student → households.Student for gradebook/billing models."""
    household_student_model = _get_household_student_model()
    if household_student_model is None or core_student is None:
        return None

    qs = household_student_model.objects.all()
    if school is not None:
        qs = _scope_qs_to_school(qs, household_student_model, school)

    first = getattr(core_student, "first_name", None)
    last = getattr(core_student, "last_name", None)
    if first and last:
        hs = qs.filter(first_name__iexact=first, last_name__iexact=last).first()
        if hs:
            return hs
    return None


def _resolve_student_pair(student_id, school):
    household_student = _query_student_by_id(_get_household_student_model(), school, student_id)
    core_student = _query_student_by_id(_get_core_student_model(), school, student_id)

    if household_student is None and core_student is not None:
        household_student = _try_get_household_student(core_student, school=school)
    if core_student is None and household_student is not None:
        core_student = _try_get_core_student(household_student, school=school)

    return household_student, core_student


def _resolve_user_student_pair(user, school):
    household_student = None
    core_student = None
    first_name = (getattr(user, "first_name", "") or "").strip()
    last_name = (getattr(user, "last_name", "") or "").strip()
    email = (getattr(user, "email", "") or "").strip()

    household_student_model = _get_household_student_model()
    if household_student_model is not None:
        hs_qs = _scope_qs_to_school(household_student_model.objects.all(), household_student_model, school)
        if email and hasattr(household_student_model, "email"):
            household_student = hs_qs.filter(email__iexact=email).first()
        if household_student is None and first_name and last_name:
            household_student = hs_qs.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
            ).first()

    core_student_model = _get_core_student_model()
    if core_student_model is not None:
        cs_qs = _scope_qs_to_school(core_student_model.objects.all(), core_student_model, school)
        if email and hasattr(core_student_model, "email"):
            core_student = cs_qs.filter(email__iexact=email).first()
        if core_student is None and first_name and last_name:
            core_student = cs_qs.filter(
                first_name__iexact=first_name,
                last_name__iexact=last_name,
            ).first()

    if household_student is None and core_student is not None:
        household_student = _try_get_household_student(core_student, school=school)
    if core_student is None and household_student is not None:
        core_student = _try_get_core_student(household_student, school=school)

    return household_student, core_student


def _get_student(student_id, school):
    household_student, core_student = _resolve_student_pair(student_id, school)
    return household_student or core_student


def _assert_student_access_or_404(request, *, household_student=None, core_student=None):
    access = resolve_household_access(request)
    if access.is_staff:
        return

    if core_student is not None:
        get_core_student_or_404_for_request(request=request, student_id=core_student.id)
        return

    household_id = getattr(household_student, "household_id", None)
    if household_id and str(household_id) in {str(item) for item in access.household_ids}:
        return

    raise Http404()


# ---------------------------------------------------------------------------
# Dashboard v2 helpers
# ---------------------------------------------------------------------------

def _safe_decimal(x, default=Decimal("0")):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _compute_weighted_percent(grade_qs):
    """
    Returns (percent_0_to_100, earned_sum, possible_sum).
    Only includes entries where points_possible > 0.
    """
    earned = Decimal("0")
    possible = Decimal("0")
    for ge in grade_qs:
        pe = _safe_decimal(getattr(ge, "points_earned", None))
        pp = _safe_decimal(getattr(ge, "points_possible", None))
        if pp > 0:
            possible += pp
            earned += pe
    if possible <= 0:
        return None, earned, possible
    return (earned / possible) * Decimal("100"), earned, possible


def _percent_to_gpa_proxy(pct):
    """Simple 4.0-scale proxy — replace later with your actual grading scale."""
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


class StudentOverview(APIView):
    permission_classes = [permissions.IsAuthenticated]
    schema = SpectacularAutoSchema()

    @extend_schema(tags=["student360"], responses=Student360OverviewResponseSerializer)
    def get(self, request, student_id):
        school = _get_school(request)
        if not school:
            return JsonResponse({"detail": "Missing or invalid school context"}, status=400)

        household_student, core_student = _resolve_student_pair(student_id, school)
        if household_student is None and core_student is None:
            return JsonResponse({"detail": "Student not found for this school."}, status=404)

        try:
            _assert_student_access_or_404(
                request,
                household_student=household_student,
                core_student=core_student,
            )
        except Http404:
            return JsonResponse({"detail": "Not found."}, status=404)

        display_student = household_student or core_student
        now = timezone.now()
        since_30 = now - timedelta(days=30)

        # Attendance summary
        attendance = {"available": False}
        if AttendanceRecord and core_student:
            try:
                qs = _scope_qs_to_school(AttendanceRecord.objects.order_by("id"), AttendanceRecord, school)
                if hasattr(AttendanceRecord, "student"):
                    qs = qs.filter(student=core_student)
                elif hasattr(AttendanceRecord, "student_id"):
                    qs = qs.filter(student_id=str(core_student.id))

                last30 = qs.filter(date__gte=since_30.date())
                total30 = last30.count()
                present30 = (
                    last30.filter(status__in=["present", "P", "Present", "PRESENT"]).count()
                    if total30
                    else 0
                )

                ytd = qs.filter(date__year=now.year)
                totaly = ytd.count()
                presenty = (
                    ytd.filter(status__in=["present", "P", "Present", "PRESENT"]).count()
                    if totaly
                    else 0
                )

                attendance = {
                    "available": True,
                    "last30_total": total30,
                    "last30_present": present30,
                    "last30_pct": (round((present30 / total30) * 100, 1) if total30 else None),
                    "ytd_total": totaly,
                    "ytd_present": presenty,
                    "ytd_pct": (round((presenty / totaly) * 100, 1) if totaly else None),
                }
            except Exception:
                logger.exception("StudentOverview attendance summary failed")

        # Finance summary (InvoiceLine is student-scoped in this repo)
        finance = {"available": False}
        try:
            from billing.models import Invoice as invoice_model, InvoiceLine as invoice_line_model
        except Exception:
            invoice_model = None
            invoice_line_model = None

        if invoice_line_model and household_student:
            try:
                line_qs = _scope_qs_to_school(
                    invoice_line_model.objects.select_related("invoice").order_by("id"),
                    invoice_line_model,
                    school,
                ).filter(student=household_student)

                open_invoice_ids: set[str] = set()
                total_due = Decimal("0.00")
                for line in line_qs[:500]:
                    invoice = getattr(line, "invoice", None)
                    if invoice is not None:
                        if hasattr(invoice, "status") and str(getattr(invoice, "status", "")).lower() == "paid":
                            continue
                        if hasattr(invoice, "is_paid") and bool(getattr(invoice, "is_paid", False)):
                            continue
                        if hasattr(invoice, "paid_at") and getattr(invoice, "paid_at", None):
                            continue
                        open_invoice_ids.add(str(invoice.id))
                    total_due += _safe_decimal(getattr(line, "amount", None))

                finance = {
                    "available": True,
                    "open_invoices": len(open_invoice_ids),
                    "open_balance_estimate": round(float(total_due), 2),
                }
            except Exception:
                logger.exception("StudentOverview finance summary failed")
        elif invoice_model and display_student:
            try:
                qs = _scope_qs_to_school(invoice_model.objects.order_by("id"), invoice_model, school)
                if hasattr(invoice_model, "student"):
                    qs = qs.filter(student=display_student)
                elif hasattr(invoice_model, "student_id"):
                    qs = qs.filter(student_id=str(display_student.id))

                total_due = Decimal("0.00")
                open_count = 0
                for inv in qs[:200]:
                    amount = getattr(inv, "balance", None)
                    if amount is None:
                        amount = getattr(inv, "amount_due", None)
                    if amount is None:
                        amount = getattr(inv, "total_amount", None)
                    total_due += _safe_decimal(amount)
                    open_count += 1

                finance = {
                    "available": True,
                    "open_invoices": open_count,
                    "open_balance_estimate": round(float(total_due), 2),
                }
            except Exception:
                logger.exception("StudentOverview invoice fallback summary failed")

        # Discipline summary
        discipline = {"available": False}
        if DisciplineIncident and core_student:
            try:
                qs = _scope_qs_to_school(DisciplineIncident.objects.order_by("id"), DisciplineIncident, school)
                if hasattr(DisciplineIncident, "student"):
                    qs = qs.filter(student=core_student)
                elif hasattr(DisciplineIncident, "student_id"):
                    qs = qs.filter(student_id=str(core_student.id))

                open_count = qs.filter(
                    status__in=["open", "OPEN", "pending", "PENDING", "investigating", "INVESTIGATING"]
                ).count()
                discipline = {
                    "available": True,
                    "incidents_total": qs.count(),
                    "incidents_open": open_count,
                }
            except Exception:
                logger.exception("StudentOverview discipline summary failed")

        # Service hours summary
        service = {"available": False}
        if ServiceEntry and core_student:
            try:
                qs = _scope_qs_to_school(ServiceEntry.objects.order_by("id"), ServiceEntry, school)
                if hasattr(ServiceEntry, "student"):
                    qs = qs.filter(student=core_student)
                elif hasattr(ServiceEntry, "student_id"):
                    qs = qs.filter(student_id=str(core_student.id))

                approved_qs = qs.filter(status__in=["approved", "APPROVED"])
                approved_hours = approved_qs.aggregate(total=Coalesce(Sum("hours"), Decimal("0")))["total"]
                service = {
                    "available": True,
                    "entries_total": qs.count(),
                    "approved_count": approved_qs.count(),
                    "pending_count": qs.filter(status__in=["pending", "PENDING"]).count(),
                    "approved_hours": round(float(_safe_decimal(approved_hours)), 2),
                }
            except Exception:
                logger.exception("StudentOverview service-hours summary failed")

        # Comms summary (school scoped, latest 3 threads)
        comms = {"available": False, "latest_threads": []}
        if MessageThread:
            try:
                qs = _scope_qs_to_school(MessageThread.objects.order_by("-created_at"), MessageThread, school)
                latest = []
                for thread in qs[:3]:
                    latest.append(
                        {
                            "id": str(getattr(thread, "id", "")),
                            "subject": getattr(thread, "subject", ""),
                            "created_at": getattr(thread, "created_at", None),
                        }
                    )
                comms = {"available": True, "latest_threads": latest}
            except Exception:
                logger.exception("StudentOverview comms summary failed")

        # --- Student Dashboard v2 (read-only, degrades gracefully) ---
        dashboard_v2 = {
            "gpa": None,
            "attendance": {"available": False},
            "current_average": None,
            "missing_assignments": 0,
            "upcoming_assignments": [],
            "today_schedule": [],
            "service_hours": {"available": False, "completed": 0, "required": 30},
            "financial": {"available": False, "balance_cents": 0},
            "alerts": [],
        }

        # Grades + assignments (households.Student-backed)
        try:
            from gradebook.models import GradeEntry as grade_entry_model
            from academics.models import Assignment as assignment_model
        except Exception:
            grade_entry_model = None
            assignment_model = None

        if grade_entry_model and assignment_model and household_student:
            try:
                today = timezone.now().date()
                future = today + timedelta(days=7)

                ge_qs = grade_entry_model.objects.filter(
                    school_id=school.id,
                    student=household_student,
                ).select_related("assignment")

                pct, _earned, _possible = _compute_weighted_percent(ge_qs)
                if pct is not None:
                    dashboard_v2["current_average"] = float(pct.quantize(Decimal("0.1")))
                    gpa = _percent_to_gpa_proxy(pct)
                    dashboard_v2["gpa"] = float(gpa) if gpa is not None else None

                ge_assignment_ids = set(
                    ge_qs.exclude(assignment=None).values_list("assignment_id", flat=True)
                )
                past_filter = {"is_published": True, "due_date__lt": today}
                if hasattr(assignment_model, "school_id"):
                    past_filter["school_id"] = str(school.id)
                elif hasattr(assignment_model, "school"):
                    past_filter["school"] = school

                past_published = assignment_model.objects.filter(**past_filter)
                missing_no_entry = past_published.exclude(id__in=ge_assignment_ids).count()
                missing_blank = ge_qs.filter(
                    assignment__is_published=True,
                    assignment__due_date__lt=today,
                ).filter(Q(points_earned__isnull=True) | Q(points_possible__isnull=True)).count()
                dashboard_v2["missing_assignments"] = int(missing_no_entry + missing_blank)

                upcoming_filter = {
                    "is_published": True,
                    "due_date__gte": today,
                    "due_date__lte": future,
                }
                if hasattr(assignment_model, "school_id"):
                    upcoming_filter["school_id"] = str(school.id)
                elif hasattr(assignment_model, "school"):
                    upcoming_filter["school"] = school

                upcoming = assignment_model.objects.filter(**upcoming_filter).order_by("due_date")[:10]
                dashboard_v2["upcoming_assignments"] = [
                    {
                        "id": str(assignment.id),
                        "title": assignment.name,
                        "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                        "points_possible": (
                            float(_safe_decimal(assignment.points_possible))
                            if assignment.points_possible is not None
                            else None
                        ),
                    }
                    for assignment in upcoming
                ]
            except Exception:
                logger.exception("StudentOverview gradebook summary failed")

        # Service hours (bridged via core.Student)
        if core_student:
            try:
                dashboard_v2["attendance"] = attendance
                dashboard_v2["service_hours"] = {
                    "available": bool(service.get("available")),
                    "completed": round(float(service.get("approved_hours") or 0), 1),
                    "required": 30,
                }
            except Exception:
                logger.debug("dashboard_v2 service-hours projection unavailable", exc_info=True)

        # Finance: InvoiceLine is student-scoped (best available)
        if household_student:
            try:
                from billing.models import InvoiceLine, Invoice as Inv

                lines = InvoiceLine.objects.filter(
                    school_id=school.id,
                    student=household_student,
                ).select_related("invoice")
                inv_filter = Q()
                if hasattr(Inv, "status"):
                    inv_filter = Q(invoice__status__in=["open", "unpaid", "pending"])
                elif hasattr(Inv, "is_paid"):
                    inv_filter = Q(invoice__is_paid=False)
                elif hasattr(Inv, "paid_at"):
                    inv_filter = Q(invoice__paid_at__isnull=True)
                if inv_filter:
                    lines = lines.filter(inv_filter)
                total_amount = lines.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
                balance_cents = int((_safe_decimal(total_amount) * Decimal("100")).quantize(Decimal("1")))
                dashboard_v2["financial"] = {"available": True, "balance_cents": balance_cents}
            except Exception:
                logger.debug("dashboard_v2 finance unavailable", exc_info=True)

        # Alerts
        try:
            avg = dashboard_v2.get("current_average")
            if avg is not None and avg < 75:
                dashboard_v2["alerts"].append(
                    {
                        "type": "academic",
                        "severity": "warning",
                        "message": "Current average is below 75%.",
                    }
                )
            if dashboard_v2.get("missing_assignments", 0) >= 3:
                dashboard_v2["alerts"].append(
                    {
                        "type": "work",
                        "severity": "warning",
                        "message": "You have 3+ missing assignments.",
                    }
                )
        except (TypeError, AttributeError):
            pass

        leadership = {"available": False}
        if service.get("available"):
            approved_hours = float(service.get("approved_hours") or 0)
            leadership = {
                "available": True,
                "readiness_score": round(min(100.0, approved_hours * 8), 1),
                "suggested_tracks": [
                    "Chapel Leadership",
                    "Peer Tutoring / Mentorship",
                    "Service & Outreach Coordinators",
                ],
                "reflection_prompt": "What does servant leadership look like in this role, and how are you serving others well?",
                "approved_hours": approved_hours,
            }

        mentorship = {"available": False}
        readiness_inputs = []
        if attendance.get("available") and attendance.get("last30_pct") is not None:
            readiness_inputs.append(float(attendance.get("last30_pct") or 0))
        if dashboard_v2.get("current_average") is not None:
            readiness_inputs.append(float(dashboard_v2.get("current_average") or 0))
        if service.get("available"):
            readiness_inputs.append(min(float(service.get("approved_hours") or 0) * 10, 100))
        if readiness_inputs:
            mentorship = {
                "available": True,
                "readiness_score": round(sum(readiness_inputs) / len(readiness_inputs), 1),
                "recommended_types": [
                    "Peer-to-Peer",
                    "Spiritual Formation Mentorship",
                    "Academic Support Mentorship",
                ],
                "core_verse": "2 Timothy 2:2",
                "reflection_prompt": "What did you learn this week that you could pass on to someone else?",
                "service_hours_can_count": True,
            }

        payload = {
            "student": {
                "id": str(student_id),
                "name": _student_name(display_student),
                "grade": _student_grade(display_student),
            },
            "attendance": attendance,
            "finance": finance,
            "discipline": discipline,
            "service_hours": service,
            "leadership": leadership,
            "mentorship": mentorship,
            "comms": comms,
            "dashboard_v2": dashboard_v2,
        }
        return JsonResponse(payload, status=200, safe=True)


class StudentSelfOverview(APIView):
    """Resolve the calling user to their student record, then delegate to StudentOverview."""

    permission_classes = [permissions.IsAuthenticated]
    schema = SpectacularAutoSchema()

    @extend_schema(tags=["student360"], responses=Student360OverviewResponseSerializer)
    def get(self, request):
        school = _get_school(request)
        if not school:
            return JsonResponse({"detail": "Missing or invalid school context"}, status=400)

        household_student, core_student = _resolve_user_student_pair(request.user, school)
        student = household_student or core_student
        if student is None:
            return JsonResponse(
                {"detail": "No student profile found for this user. Contact your school administrator."},
                status=404,
            )

        delegate = StudentOverview()
        delegate.request = request
        delegate.args = []
        delegate.kwargs = {"student_id": student.id}
        return delegate.get(request, student_id=student.id)
