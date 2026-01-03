from django.conf import settings
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from aid.models import AidApplication, AidAward, AidDocument
from core.models import (
    AcademicYear,
    Enrollment,
    Family,
    GradeLevel,
    LedgerEntry,
    StudentTuition,
    UserRole,
)


ALLOWED_ROLE_CODES = {
    "ROLE_AID_DIRECTOR",
    "ROLE_FINANCE_DIRECTOR",
    "ROLE_REGISTRAR",
    "ROLE_HEAD_OF_SCHOOL",
}


def crown_director_allowed(request):
    """
    Check if user is allowed to access director APIs.
    
    Allows:
    1. Dev mode (CROWN_DEV_OPEN_API=1 env var)
    2. Superuser
    3. Users with director role codes
    """
    user = request.user
    
    # Dev override (explicit toggle)
    if getattr(settings, "CROWN_DEV_OPEN_API", False):
        return True
    
    # Superuser always allowed
    if user and getattr(user, "is_superuser", False):
        return True
    
    # Check authenticated + role
    if not user or not user.is_authenticated:
        return False
    
    return UserRole.objects.filter(user=user, role_code__in=ALLOWED_ROLE_CODES).exists()


def user_has_director_role(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    return UserRole.objects.filter(user=user, role_code__in=ALLOWED_ROLE_CODES).exists()


def resolve_academic_year(school_id, academic_year_id=None):
    if academic_year_id:
        return AcademicYear.objects.filter(id=academic_year_id, school_id=school_id).first()
    return AcademicYear.objects.filter(school_id=school_id, is_current=True).order_by("-start_date").first()



@api_view(["GET"])
@permission_classes([AllowAny])
def aid_summary(request):
    school_id = request.GET.get("school_id")
    academic_year_id = request.GET.get("academic_year_id")

    if not school_id:
        return Response({"detail": "school_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check authorization (dev mode + superuser + role-based)
    if not crown_director_allowed(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    academic_year = resolve_academic_year(school_id, academic_year_id)
    if not academic_year:
        return Response({"detail": "academic_year not found for school"}, status=status.HTTP_400_BAD_REQUEST)

    ay_id = academic_year.id

    apps = AidApplication.objects.filter(school_id=school_id, academic_year_id=ay_id)
    awards = AidAward.objects.filter(school_id=school_id, academic_year_id=ay_id)
    docs_missing = AidDocument.objects.filter(
        school_id=school_id,
        aid_application__academic_year_id=ay_id,
        received=False,
    )

    data = {
        "applications": {
            "total": apps.count(),
            "submitted": apps.filter(status=AidApplication.STATUS_SUBMITTED).count(),
            "needs_info": apps.filter(status=AidApplication.STATUS_NEEDS_INFO).count(),
            "under_review": apps.filter(status=AidApplication.STATUS_UNDER_REVIEW).count(),
            "approved": apps.filter(status=AidApplication.STATUS_APPROVED).count(),
            "denied": apps.filter(status=AidApplication.STATUS_DENIED).count(),
        },
        "awards": {
            "total_awards": awards.count(),
            "offered_not_accepted": awards.filter(decision_status=AidAward.DECISION_OFFERED).count(),
            "accepted_not_posted": awards.filter(decision_status=AidAward.DECISION_ACCEPTED, ledger_entry__isnull=True).count(),
            "posted_to_ledger": awards.filter(ledger_entry__isnull=False).count(),
            "total_awarded_cents": int(
                awards.aggregate(total=Coalesce(Sum("awarded_cents"), 0)).get("total", 0)
            ),
        },
        "documents": {
            "missing_documents_count": docs_missing.count(),
        },
    }

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def finance_summary(request):
    school_id = request.GET.get("school_id")
    academic_year_id = request.GET.get("academic_year_id")

    if not school_id:
        return Response({"detail": "school_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check authorization (dev mode + superuser + role-based)
    if not crown_director_allowed(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    academic_year = resolve_academic_year(school_id, academic_year_id)
    if not academic_year:
        return Response({"detail": "academic_year not found for school"}, status=status.HTTP_400_BAD_REQUEST)

    ay_id = academic_year.id

    tuition_qs = StudentTuition.objects.filter(school_id=school_id, academic_year_id=ay_id)
    awards_qs = AidAward.objects.filter(school_id=school_id, academic_year_id=ay_id)
    ledger_qs = LedgerEntry.objects.filter(school_id=school_id, academic_year_id=ay_id)

    gross_tuition = tuition_qs.aggregate(total=Coalesce(Sum("net_annual_cents"), 0)).get("total", 0)

    total_aid_awarded = awards_qs.aggregate(total=Coalesce(Sum("awarded_cents"), 0)).get("total", 0)

    total_aid_posted = (
        ledger_qs.filter(account__code="AID").aggregate(total=Coalesce(Sum("amount_cents"), 0)).get("total", 0)
    )

    credits = ledger_qs.aggregate(total=Coalesce(Sum("amount_cents", filter=Q(amount_cents__lt=0)), 0)).get(
        "total", 0
    )
    debits = ledger_qs.aggregate(total=Coalesce(Sum("amount_cents", filter=Q(amount_cents__gt=0)), 0)).get(
        "total", 0
    )

    data = {
        "tuition": {
            "students_billed": tuition_qs.count(),
            "gross_tuition_cents": int(gross_tuition),
        },
        "aid": {
            "total_aid_awarded_cents": int(total_aid_awarded),
            "total_aid_posted_cents": int(total_aid_posted),
        },
        "ledger": {
            "net_receivables_cents": int(debits + credits),
            "total_credits_cents": int(credits),
            "total_debits_cents": int(debits),
        },
    }

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def registrar_summary(request):
    school_id = request.GET.get("school_id")
    academic_year_id = request.GET.get("academic_year_id")

    if not school_id:
        return Response({"detail": "school_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check authorization (dev mode + superuser + role-based)
    if not crown_director_allowed(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    academic_year = resolve_academic_year(school_id, academic_year_id)
    if not academic_year:
        return Response({"detail": "academic_year not found for school"}, status=status.HTTP_400_BAD_REQUEST)

    ay_id = academic_year.id

    enrollments = Enrollment.objects.filter(
        school_id=school_id,
        academic_year_id=ay_id,
        status="ENROLLED",
    )

    grade_codes = [code for code, _ in GradeLevel.GRADE_CHOICES]
    grade_counts = {code: 0 for code in grade_codes}

    for row in enrollments.values("grade_level__code").annotate(c=Count("id")):
        code = row.get("grade_level__code")
        if code:
            grade_counts[code] = row.get("c", 0)

    families_count = Family.objects.filter(school_id=school_id).count()

    data = {
        "enrollment": {
            "total_students": enrollments.count(),
            "by_grade": grade_counts,
        },
        "families": {
            "total_families": families_count,
        },
    }

    return Response(data)


@api_view(["GET"])
@permission_classes([AllowAny])
def director_dashboard(request):
    """
    Unified dashboard payload for Head of School / Directors.
    Combines aid, finance, registrar summaries into one response.
    Requires: school_id and year_id query parameters.
    """
    if not crown_director_allowed(request):
        return Response(
            {"error": "Unauthorized. Director access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    school_id = request.query_params.get("school_id")
    year_id = request.query_params.get("year_id") or request.query_params.get("academic_year_id")

    aid_resp = aid_summary(request)
    finance_resp = finance_summary(request)
    registrar_resp = registrar_summary(request)

    return Response({
        "meta": {
            "school_id": school_id,
            "year_id": year_id,
        },
        "sections": {
            "aid": getattr(aid_resp, "data", aid_resp.data if hasattr(aid_resp, "data") else aid_resp),
            "finance": getattr(finance_resp, "data", finance_resp.data if hasattr(finance_resp, "data") else finance_resp),
            "registrar": getattr(registrar_resp, "data", registrar_resp.data if hasattr(registrar_resp, "data") else registrar_resp),
        },
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def director_priority(request):
    """
    Priority queue for directors: the next items to work, ordered and limited.
    Shows top 10 actionable items for aid, finance, and registrar directors.
    """
    if not crown_director_allowed(request):
        return Response(
            {"error": "Unauthorized. Director access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    school_id = request.query_params.get("school_id")
    academic_year_id = request.query_params.get("year_id") or request.query_params.get("academic_year_id")

    academic_year = resolve_academic_year(school_id, academic_year_id)

    # --- Aid priorities ---
    needs_info_apps = (
        AidApplication.objects
        .filter(school_id=school_id, academic_year=academic_year, status=AidApplication.STATUS_NEEDS_INFO)
        .select_related("family")
        .order_by("-submitted_at")[:10]
    )

    under_review_apps = (
        AidApplication.objects
        .filter(school_id=school_id, academic_year=academic_year, status=AidApplication.STATUS_UNDER_REVIEW)
        .select_related("family")
        .order_by("-submitted_at")[:10]
    )

    accepted_not_posted_awards = (
        AidAward.objects
        .filter(
            school_id=school_id,
            academic_year=academic_year,
            decision_status=AidAward.DECISION_ACCEPTED,
            ledger_entry__isnull=True,
        )
        .select_related("student", "student__family")
        .order_by("-decided_at", "-created_at")[:10]
    )

    # --- Finance priorities ---
    # Families with largest net balance due (positive receivable)
    # Assumes LedgerEntry.amount_cents: debits positive, credits negative
    family_balances = (
        LedgerEntry.objects
        .filter(school_id=school_id, academic_year=academic_year, family__isnull=False)
        .values("family_id", "family__family_name")
        .annotate(balance_cents=Sum("amount_cents"))
        .order_by("-balance_cents")[:10]
    )

    # Students billed check
    billed_count = StudentTuition.objects.filter(school_id=school_id, academic_year=academic_year).count()

    # --- Registrar priorities ---
    # Enrollment with missing grade
    enrollments_missing_grade = (
        Enrollment.objects
        .filter(school_id=school_id, academic_year=academic_year, status='ENROLLED')
        .filter(grade_level__isnull=True)
        .count()
    )

    # Build payload
    return Response({
        "meta": {
            "school_id": school_id,
            "year_id": academic_year_id,
        },
        "aid": {
            "needs_info_applications": [
                {
                    "application_id": str(a.id),
                    "family": getattr(a.family, "family_name", None),
                    "submitted_at": a.submitted_at,
                }
                for a in needs_info_apps
            ],
            "under_review_applications": [
                {
                    "application_id": str(a.id),
                    "family": getattr(a.family, "family_name", None),
                    "submitted_at": a.submitted_at,
                }
                for a in under_review_apps
            ],
            "accepted_not_posted_awards": [
                {
                    "award_id": str(w.id),
                    "student": f"{w.student.first_name} {w.student.last_name}" if w.student else None,
                    "family": getattr(getattr(w.student, "family", None), "family_name", None),
                    "awarded_cents": w.awarded_cents,
                }
                for w in accepted_not_posted_awards
            ],
        },
        "finance": {
            "top_balances_due": list(family_balances),
            "students_billed_count": billed_count,
        },
        "registrar": {
            "enrollments_missing_grade_count": enrollments_missing_grade,
        }
    })
