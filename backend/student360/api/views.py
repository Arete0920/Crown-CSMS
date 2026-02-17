from __future__ import annotations

from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import permissions

from core.models import School

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
    except Exception:
        pass
    try:
        from core.models import Student
        candidates.append(Student)
    except Exception:
        pass
    return candidates[0] if candidates else None

def _get_student(student_id, school):
    Student = _find_student_model()
    if not Student:
        return None
    qs = Student.objects.all()
    # school scoping if possible
    if hasattr(Student, "school"):
        qs = qs.filter(school=school)
    elif hasattr(Student, "school_id"):
        qs = qs.filter(school_id=str(school.id))
    try:
        return qs.get(id=student_id)
    except Exception:
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
            if hasattr(AttendanceRecord, "school_id"):
                qs = qs.filter(school_id=str(school.id))
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
            if hasattr(Invoice, "school_id"):
                qs = qs.filter(school_id=str(school.id))
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
                except Exception:
                    pass
            finance["open_balance_estimate"] = round(total_due, 2)

        # Discipline summary
        discipline = {"available": False}
        if DisciplineIncident and student:
            discipline["available"] = True
            qs = DisciplineIncident.objects.all()
            if hasattr(DisciplineIncident, "school_id"):
                qs = qs.filter(school_id=str(school.id))
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
            if hasattr(ServiceEntry, "school_id"):
                qs = qs.filter(school_id=str(school.id))
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
                except Exception:
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
            if hasattr(MessageThread, "school"):
                qs = qs.filter(school=school)
            elif hasattr(MessageThread, "school_id"):
                qs = qs.filter(school_id=str(school.id))
            qs = qs.order_by("-created_at")[:3]
            latest = []
            for t in qs:
                latest.append({
                    "id": str(getattr(t, "id")),
                    "subject": getattr(t, "subject", ""),
                    "created_at": getattr(t, "created_at", None),
                })
            comms["latest_threads"] = latest

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
        }
        return JsonResponse(payload, status=200, safe=True)
