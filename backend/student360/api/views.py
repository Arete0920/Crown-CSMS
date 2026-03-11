from __future__ import annotations

import logging
from datetime import timedelta
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import permissions

from core.models import School
from django.core.exceptions import ImproperlyConfigured


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


# Optional imports (only used if present)
try:
    from attendance.models import AttendanceRecord
except Exception:
    AttendanceRecord = None

try:
    from billing.models import Invoice
except Exception:
    Invoice = None

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
        return School.objects.get(id=sid)
    except School.DoesNotExist:
        return None

def _find_student_model():
    # Best-effort: try common places without hard failing.
    # If this returns None, the endpoint still responds with placeholders.
    candidates = []
    try:
        from students.models import Student
        candidates.append(Student)
    except ImportError:
        logger.debug("students.Student unavailable", exc_info=True)
    try:
        from core.models import Student
        candidates.append(Student)
    except ImportError:
        logger.debug("core.Student unavailable", exc_info=True)
    return candidates[0] if candidates else None

def _get_student(student_id, school):
    Student = _find_student_model()
    if not Student:
        return None
    qs = Student.objects.filter()
    # school scoping if possible
    if hasattr(Student, "school"):
        qs = qs.filter(school=school)
    elif hasattr(Student, "school_id"):
        qs = qs.filter(school_id=str(school.id))
    try:
        return qs.get(id=student_id)
    except Exception:
        return None


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


def _try_get_core_student(households_student):
    """Bridge households.Student → core.Student for ServiceEntry FK (legacy)."""
    try:
        from core.models import Student as CoreStudent
    except Exception:
        return None
    email = getattr(households_student, "email", None)
    if email:
        cs = CoreStudent.objects.filter(email__iexact=email).first()
        if cs:
            return cs
    first = getattr(households_student, "first_name", None)
    last = getattr(households_student, "last_name", None)
    if first and last:
        cs = CoreStudent.objects.filter(first_name__iexact=first, last_name__iexact=last).first()
        if cs:
            return cs
    return None


class StudentOverview(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, student_id):
        school = _get_school(request)
        if not school:
            return JsonResponse({"detail": "Missing or invalid school context"}, status=400)

        student = _get_student(student_id, school)

        now = timezone.now()
        since_30 = now - timedelta(days=30)

        # Attendance summary
        attendance = {"available": False}
        if AttendanceRecord and student:
            attendance["available"] = True
            qs = AttendanceRecord.objects.all()
            qs = _scope_qs_to_school(qs, AttendanceRecord, school)
            # common field names: student or student_id
            if hasattr(AttendanceRecord, "student"):
                qs = qs.filter(student=student)
            elif hasattr(AttendanceRecord, "student_id"):
                qs = qs.filter(student_id=str(student.id))

            last30 = qs.filter(date__gte=since_30.date())
            total30 = last30.count()
            present30 = last30.filter(status__in=["present", "P", "Present"]).count() if total30 else 0

            ytd = qs.filter(date__year=now.year)
            totaly = ytd.count()
            presenty = ytd.filter(status__in=["present", "P", "Present"]).count() if totaly else 0

            attendance.update({
                "last30_total": total30,
                "last30_present": present30,
                "last30_pct": (round((present30/total30)*100, 1) if total30 else None),
                "ytd_total": totaly,
                "ytd_present": presenty,
                "ytd_pct": (round((presenty/totaly)*100, 1) if totaly else None),
            })

        # Finance summary (invoice-centric)
        finance = {"available": False}
        if Invoice and student:
            finance["available"] = True
            qs = Invoice.objects.all()
            qs = _scope_qs_to_school(qs, Invoice, school)
            if hasattr(Invoice, "student"):
                qs = qs.filter(student=student)
            elif hasattr(Invoice, "student_id"):
                qs = qs.filter(student_id=str(student.id))

            open_qs = qs.exclude(status__in=["paid", "PAID"])
            finance.update({
                "open_invoices": open_qs.count(),
            })
            # If amount/balance fields exist, compute rough totals
            total_due = 0.0
            for inv in open_qs[:200]:
                amt = getattr(inv, "balance", None)
                if amt is None:
                    amt = getattr(inv, "amount_due", None)
                if amt is None:
                    amt = getattr(inv, "total", None)
                try:
                    total_due += float(amt or 0)
                except (ValueError, TypeError):
                    pass
            finance["open_balance_estimate"] = round(total_due, 2)

        # Discipline summary
        discipline = {"available": False}
        if DisciplineIncident and student:
            discipline["available"] = True
            qs = DisciplineIncident.objects.all()
            qs = _scope_qs_to_school(qs, DisciplineIncident, school)
            if hasattr(DisciplineIncident, "student"):
                qs = qs.filter(student=student)
            elif hasattr(DisciplineIncident, "student_id"):
                qs = qs.filter(student_id=str(student.id))

            open_count = qs.filter(status__in=["open", "OPEN", "pending", "PENDING"]).count()
            discipline.update({
                "incidents_total": qs.count(),
                "incidents_open": open_count,
            })

        # Service hours summary
        service = {"available": False}
        if ServiceEntry and student:
            service["available"] = True
            qs = ServiceEntry.objects.all()
            qs = _scope_qs_to_school(qs, ServiceEntry, school)
            if hasattr(ServiceEntry, "student"):
                qs = qs.filter(student=student)
            elif hasattr(ServiceEntry, "student_id"):
                qs = qs.filter(student_id=str(student.id))

            approved = qs.filter(status__in=["approved", "APPROVED"]).count()
            pending = qs.filter(status__in=["pending", "PENDING"]).count()
            # try to sum hours if field exists
            approved_hours = 0.0
            for e in qs.filter(status__in=["approved", "APPROVED"])[:500]:
                h = getattr(e, "hours", None)
                try:
                    approved_hours += float(h or 0)
                except (ValueError, TypeError):
                    pass

            service.update({
                "entries_total": qs.count(),
                "approved_count": approved,
                "pending_count": pending,
                "approved_hours": round(approved_hours, 2),
            })

        # Comms summary (school scoped, latest 3 threads)
        comms = {"available": False, "latest_threads": []}
        if MessageThread:
            comms["available"] = True
            qs = MessageThread.objects.all()
            qs = _scope_qs_to_school(qs, MessageThread, school)
            qs = qs.order_by("-created_at")[:3]
            latest = []
            for t in qs:
                latest.append({
                    "id": str(getattr(t, "id")),
                    "subject": getattr(t, "subject", ""),
                    "created_at": getattr(t, "created_at", None),
                })
            comms["latest_threads"] = latest

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

        # Grades + assignments (real data)
        try:
            from gradebook.models import GradeEntry
            from academics.models import Assignment
        except Exception:
            GradeEntry = None
            Assignment = None

        if GradeEntry and Assignment and student:
            today = timezone.now().date()
            future = today + timedelta(days=7)

            ge_qs = GradeEntry.objects.filter(student=student).select_related("assignment")

            pct, _earned, _possible = _compute_weighted_percent(ge_qs)
            if pct is not None:
                dashboard_v2["current_average"] = float(pct.quantize(Decimal("0.1")))
                gpa = _percent_to_gpa_proxy(pct)
                dashboard_v2["gpa"] = float(gpa) if gpa is not None else None

            # Missing: published, past due, no entry or entry lacks earned score
            ge_assignment_ids = set(
                ge_qs.exclude(assignment=None).values_list("assignment_id", flat=True)
            )
            past_filter = {"is_published": True, "due_date__lt": today}
            if hasattr(Assignment, "school_id"):
                past_filter["school_id"] = str(school.id)
            elif hasattr(Assignment, "school"):
                past_filter["school"] = school
            past_published = Assignment.objects.filter(**past_filter)
            missing_no_entry = past_published.exclude(id__in=ge_assignment_ids).count()
            missing_blank = ge_qs.filter(
                assignment__is_published=True,
                assignment__due_date__lt=today,
            ).filter(Q(points_earned__isnull=True) | Q(points_possible__isnull=True)).count()
            dashboard_v2["missing_assignments"] = int(missing_no_entry + missing_blank)

            # Upcoming: next 7 days
            upcoming_filter = {
                "is_published": True,
                "due_date__gte": today,
                "due_date__lte": future,
            }
            if hasattr(Assignment, "school_id"):
                upcoming_filter["school_id"] = str(school.id)
            elif hasattr(Assignment, "school"):
                upcoming_filter["school"] = school
            upcoming = Assignment.objects.filter(**upcoming_filter).order_by("due_date")[:10]
            dashboard_v2["upcoming_assignments"] = [
                {
                    "id": str(a.id),
                    "title": a.name,
                    "due_date": a.due_date.isoformat() if a.due_date else None,
                    "points_possible": float(_safe_decimal(a.points_possible)) if a.points_possible is not None else None,
                }
                for a in upcoming
            ]

        # Service hours (bridged via core.Student)
        try:
            from servicehours.models import ServiceEntry as SE
            core_student = _try_get_core_student(student) if student else None
            if core_student:
                approved_qs = SE.objects.filter(student=core_student, status="approved")
                total_hours = float(
                    approved_qs.aggregate(t=Coalesce(Sum("hours"), Decimal("0")))[ "t"]
                )
                dashboard_v2["service_hours"] = {
                    "available": True,
                    "completed": round(total_hours, 1),
                    "required": 30,
                }
        except Exception:
            logger.debug("dashboard_v2 service hours unavailable", exc_info=True)

        # Finance: InvoiceLine is student-scoped (best available)
        try:
            from billing.models import InvoiceLine, Invoice as Inv
            lines = InvoiceLine.objects.filter(student=student).select_related("invoice")
            inv_filter = Q()
            if hasattr(Inv, "status"):
                inv_filter = Q(invoice__status__in=["open", "unpaid", "pending"])
            elif hasattr(Inv, "is_paid"):
                inv_filter = Q(invoice__is_paid=False)
            elif hasattr(Inv, "paid_at"):
                inv_filter = Q(invoice__paid_at__isnull=True)
            if inv_filter:
                lines = lines.filter(inv_filter)
            total_amount = lines.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))[ "total"]
            balance_cents = int((_safe_decimal(total_amount) * Decimal("100")).quantize(Decimal("1")))
            dashboard_v2["financial"] = {"available": True, "balance_cents": balance_cents}
        except Exception:
            logger.debug("dashboard_v2 finance unavailable", exc_info=True)

        # Alerts
        try:
            avg = dashboard_v2.get("current_average")
            if avg is not None and avg < 75:
                dashboard_v2["alerts"].append({"type": "academic", "severity": "warning", "message": "Current average is below 75%."})
            if dashboard_v2.get("missing_assignments", 0) >= 3:
                dashboard_v2["alerts"].append({"type": "work", "severity": "warning", "message": "You have 3+ missing assignments."})
        except (TypeError, AttributeError):
            pass

        payload = {
            "student": {
                "id": str(getattr(student, "id")) if student else str(student_id),
                "name": (
                    getattr(student, "full_name", None)
                    or f"{getattr(student,'first_name','')}".strip() + " " + f"{getattr(student,'last_name','')}".strip()
                    if student else "Unknown Student"
                ),
                "grade": getattr(student, "grade_level", None) if student else None,
            },
            "attendance": attendance,
            "finance": finance,
            "discipline": discipline,
            "service_hours": service,
            "comms": comms,
            "dashboard_v2": dashboard_v2,
        }
        return JsonResponse(payload, status=200, safe=True)


class StudentSelfOverview(APIView):
    """Resolve the calling user to their student record, then delegate to StudentOverview."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school(request)
        if not school:
            return JsonResponse({"detail": "Missing or invalid school context"}, status=400)

        user = request.user
        first_name = getattr(user, "first_name", "").strip()
        last_name = getattr(user, "last_name", "").strip()

        Student = _find_student_model()
        if not Student:
            return JsonResponse({"detail": "Student model unavailable"}, status=503)

        qs = Student.objects.filter()
        qs = _scope_qs_to_school(qs, Student, school)

        student = None
        if first_name and last_name:
            student = qs.filter(first_name__iexact=first_name, last_name__iexact=last_name).first()

        if student is None:
            return JsonResponse(
                {"detail": "No student profile found for this user. Contact your school administrator."},
                status=404,
            )

        # Delegate to the full overview view using the resolved student_id
        delegate = StudentOverview()
        delegate.request = request
        delegate.args = []
        delegate.kwargs = {"student_id": student.id}
        return delegate.get(request, student_id=student.id)
