from django.conf import settings
from django.db import transaction
from django.db.models import Count, Sum, Q
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from aid.models import AidApplication, AidAward, AidDocument
from admissions.models import AdmissionsApplication
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
    "AID_DIRECTOR",
    "FINANCE_DIRECTOR",
    "REGISTRAR",
    "HEAD_OF_SCHOOL",
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
    
    user_id = getattr(user, "id", None)
    if not user_id:
        return False
    return UserRole.objects.filter(user_id=user_id, role_code__in=ALLOWED_ROLE_CODES).exists()


def user_has_director_role(user):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    user_id = getattr(user, "id", None)
    if not user_id:
        return False
    return UserRole.objects.filter(user_id=user_id, role_code__in=ALLOWED_ROLE_CODES).exists()


def resolve_academic_year(school_id, academic_year_id=None):
    if academic_year_id:
        return AcademicYear.objects.filter(id=academic_year_id, school_id=school_id).first()
    return AcademicYear.objects.filter(school_id=school_id, is_current=True).order_by("-start_date").first()


def build_director_priority_snapshot(school_id, academic_year):
    """
    Build a lightweight snapshot of priority items for the UI.
    Called after director actions to refresh the queue without a second API call.
    """
    if not academic_year:
        return None
    
    admissions_needs_info_apps = (
        AdmissionsApplication.objects
        .filter(
            school_id=school_id,
            academic_year=academic_year,
            status=AdmissionsApplication.STATUS_NEEDS_INFO,
        )
        .select_related("family")
        .order_by("-submitted_at")[:10]
    )

    admissions_under_review_apps = (
        AdmissionsApplication.objects
        .filter(
            school_id=school_id,
            academic_year=academic_year,
            status=AdmissionsApplication.STATUS_UNDER_REVIEW,
        )
        .select_related("family")
        .order_by("-submitted_at")[:10]
    )

    return {
        "aid": {
            "needs_info": list(
                AidApplication.objects.filter(
                    school_id=school_id,
                    academic_year=academic_year,
                    status=AidApplication.STATUS_NEEDS_INFO,
                )
                .order_by("-submitted_at")
                .values("id", "status")[:10]
            ),
            "accepted_not_posted": list(
                AidAward.objects.filter(
                    school_id=school_id,
                    academic_year=academic_year,
                    decision_status=AidAward.DECISION_ACCEPTED,
                    ledger_entry__isnull=True,
                )
                .order_by("-decided_at", "-created_at")
                .values("id", "awarded_cents")[:10]
            ),
        },
        "admissions": {
            "needs_info_applications": [
                {
                    "application_id": str(a.id),
                    "family": getattr(a.family, "family_name", None),
                    "submitted_at": a.submitted_at,
                }
                for a in admissions_needs_info_apps
            ],
            "under_review_applications": [
                {
                    "application_id": str(a.id),
                    "family": getattr(a.family, "family_name", None),
                    "submitted_at": a.submitted_at,
                }
                for a in admissions_under_review_apps
            ],
        },
        "finance": {
            "balance_due": list(
                LedgerEntry.objects
                .filter(school_id=school_id, academic_year=academic_year, family__isnull=False)
                .values("family_id", "family__family_name")
                .annotate(balance_cents=Sum("amount_cents"))
                .filter(balance_cents__gt=0)
                .order_by("-balance_cents")[:10]
            )
        }
    }

@api_view(["GET"])
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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
@permission_classes([IsAuthenticated])
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

    if not school_id:
        return Response({"detail": "school_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Resolve academic year
        academic_year = resolve_academic_year(school_id, year_id)
        if not academic_year:
            return Response({"detail": "academic_year not found for school"}, status=status.HTTP_400_BAD_REQUEST)

        ay_id = academic_year.id

        # --- AID SUMMARY ---
        apps = AidApplication.objects.filter(school_id=school_id, academic_year_id=ay_id)
        awards = AidAward.objects.filter(school_id=school_id, academic_year_id=ay_id)
        docs_missing = AidDocument.objects.filter(
            school_id=school_id,
            aid_application__academic_year_id=ay_id,
            received=False,
        )

        aid_data = {
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

        # --- FINANCE SUMMARY ---
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

        finance_data = {
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

        # --- REGISTRAR SUMMARY ---
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

        registrar_data = {
            "enrollment": {
                "total_students": enrollments.count(),
                "by_grade": grade_counts,
            },
            "families": {
                "total_families": families_count,
            },
        }

        return Response({
            "meta": {
                "school_id": school_id,
                "year_id": year_id,
            },
            "sections": {
                "aid": aid_data,
                "finance": finance_data,
                "registrar": registrar_data,
            },
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {"error": f"Dashboard error: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
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

    # --- Admissions priorities (cloned from Aid pattern) ---
    admissions_needs_info_apps = (
        AdmissionsApplication.objects
        .filter(school_id=school_id, academic_year=academic_year, status=AdmissionsApplication.STATUS_NEEDS_INFO)
        .select_related("family")
        .order_by("-submitted_at")[:10]
    )

    admissions_under_review_apps = (
        AdmissionsApplication.objects
        .filter(school_id=school_id, academic_year=academic_year, status=AdmissionsApplication.STATUS_UNDER_REVIEW)
        .select_related("family")
        .order_by("-submitted_at")[:10]
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

    # --- Priority scoring formula ---
    now = timezone.now()

    def days_waiting(dt):
        if not dt:
            return 0
        delta = now - dt
        return max(0, int(delta.total_seconds() // 86400))

    # Build scored items (Aid)
    aid_items = []

    for a in needs_info_apps:
        score = 100 + (days_waiting(a.submitted_at) * 3)  # missing docs are urgent
        aid_items.append({
            "type": "AID_APPLICATION_NEEDS_INFO",
            "score": score,
            "id": str(a.id),
            "family": getattr(a.family, "family_name", None),
            "submitted_at": a.submitted_at,
            "summary": "Application needs info (missing documents).",
        })

    for a in under_review_apps:
        score = 60 + (days_waiting(a.submitted_at) * 2)
        aid_items.append({
            "type": "AID_APPLICATION_UNDER_REVIEW",
            "score": score,
            "id": str(a.id),
            "family": getattr(a.family, "family_name", None),
            "submitted_at": a.submitted_at,
            "summary": "Application under review.",
        })

    for w in accepted_not_posted_awards:
        # Bigger awards should rise (posting impacts billing immediately)
        award_dollars = (w.awarded_cents or 0) / 100
        score = 90 + min(40, int(award_dollars // 500))  # +1 per $500 up to +40
        aid_items.append({
            "type": "AID_AWARD_ACCEPTED_NOT_POSTED",
            "score": score,
            "id": str(w.id),
            "student": (f"{w.student.first_name} {w.student.last_name}" if w.student else None),
            "family": getattr(getattr(w.student, "family", None), "family_name", None),
            "awarded_cents": w.awarded_cents,
            "summary": "Accepted award not posted to ledger.",
        })

    # Build scored items (Admissions - cloned from Aid pattern)
    admissions_items = []

    for a in admissions_needs_info_apps:
        score = 100 + (days_waiting(a.submitted_at) * 3)  # missing docs are urgent
        admissions_items.append({
            "type": "ADMISSIONS_APPLICATION_NEEDS_INFO",
            "score": score,
            "id": str(a.id),
            "family": getattr(a.family, "family_name", None),
            "submitted_at": a.submitted_at,
            "summary": "Admissions application needs info (missing documents).",
        })

    for a in admissions_under_review_apps:
        score = 60 + (days_waiting(a.submitted_at) * 2)
        admissions_items.append({
            "type": "ADMISSIONS_APPLICATION_UNDER_REVIEW",
            "score": score,
            "id": str(a.id),
            "family": getattr(a.family, "family_name", None),
            "submitted_at": a.submitted_at,
            "summary": "Admissions application under review.",
        })

    # Build scored items (Finance)
    finance_items = []
    for row in list(family_balances):
        balance_cents = row.get("balance_cents") or 0
        # Only balances > 0 are receivables to chase
        if balance_cents <= 0:
            continue
        balance_dollars = balance_cents / 100
        score = 70 + min(60, int(balance_dollars // 500))  # +1 per $500 up to +60
        finance_items.append({
            "type": "FINANCE_BALANCE_DUE",
            "score": score,
            "family_id": str(row.get("family_id")),
            "family": row.get("family__family_name"),
            "balance_cents": balance_cents,
            "summary": "Family balance due requires follow-up.",
        })

    # Build scored items (Registrar)
    registrar_items = []
    if enrollments_missing_grade > 0:
        score = 50 + min(50, enrollments_missing_grade)  # scale with count
        registrar_items.append({
            "type": "REGISTRAR_MISSING_GRADE",
            "score": score,
            "count": enrollments_missing_grade,
            "summary": "Enrollments missing grade assignment.",
        })

    # Merge + sort by score
    worklist = sorted(
        aid_items + admissions_items + finance_items + registrar_items,
        key=lambda x: x["score"],
        reverse=True
    )[:10]

    # Build payload
    return Response({
        "meta": {
            "school_id": school_id,
            "year_id": academic_year_id,
        },
        "worklist_top_10": worklist,
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
        "admissions": {
            "needs_info_applications": [
                {
                    "application_id": str(a.id),
                    "family": getattr(a.family, "family_name", None),
                    "submitted_at": a.submitted_at,
                }
                for a in admissions_needs_info_apps
            ],
            "under_review_applications": [
                {
                    "application_id": str(a.id),
                    "family": getattr(a.family, "family_name", None),
                    "submitted_at": a.submitted_at,
                }
                for a in admissions_under_review_apps
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def director_actions(request):
    """
    Endpoint for director/Head of School actions.
    
    Supported actions:
    - POST_ACCEPTED_AWARDS: Post accepted award(s) to ledger
    
    Request body:
    {
        "action": "POST_ACCEPTED_AWARDS",
        "school_id": "...",
        "year_id": "...",
        "ids": ["award_id1", "award_id2", ...]
    }
    """
    # Security: director actions must never be callable anonymously.
    # Even if CROWN_DEV_OPEN_API is enabled, require an authenticated staff user.
    if not getattr(request.user, "is_authenticated", False):
        return Response(
            {"error": "Authentication required"},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not getattr(request.user, "is_staff", False) and not getattr(request.user, "is_superuser", False):
        return Response(
            {"error": "Forbidden. Staff access required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if not crown_director_allowed(request):
        return Response(
            {"error": "Unauthorized. Director access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    try:
        action = request.data.get("action")
        school_id = request.data.get("school_id")
        year_id = request.data.get("year_id")
        ids = request.data.get("ids", [])
        
        if not action:
            return Response(
                {"error": "Missing required field: action"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if action == "POST_ACCEPTED_AWARDS":
            if not ids:
                return Response(
                    {"error": "Missing required field: ids"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                posted_count = 0
                errors = []
                
                for award_id in ids:
                    try:
                        award = AidAward.objects.get(id=award_id, school_id=school_id)

                        if year_id and str(award.academic_year_id) != str(year_id):
                            errors.append({
                                "award_id": award_id,
                                "error": "Award does not belong to specified academic year",
                            })
                            continue

                        if award.decision_status != AidAward.DECISION_ACCEPTED:
                            errors.append({
                                "award_id": award_id,
                                "error": "Award is not ACCEPTED",
                            })
                            continue

                        was_unposted = award.ledger_entry_id is None

                        actor_user = request.user if getattr(request.user, "is_authenticated", False) else None
                        
                        # Post to ledger (idempotent; will not double-post)
                        award.mark_accepted_and_post(actor_user=actor_user)

                        if was_unposted and award.ledger_entry_id is not None:
                            posted_count += 1
                    except AidAward.DoesNotExist:
                        errors.append({
                            "award_id": award_id,
                            "error": "Award not found",
                        })
                    except (TypeError, ValueError):
                        errors.append({
                            "award_id": award_id,
                            "error": "Award not found",
                        })
                    except Exception as e:
                        errors.append({
                            "award_id": award_id,
                            "error": str(e),
                        })
                
                return Response({
                    "action": action,
                    "posted_count": posted_count,
                    "total_requested": len(ids),
                    "errors": errors if errors else None,
                })
        
        elif action == "AID_GENERATE_NEEDS_INFO_EMAILS":
            # Generate email drafts for needs-info applications (no sending)
            drafts = []
            failures = []
            
            # Fetch academic year if provided
            academic_year = None
            if year_id:
                from core.models import AcademicYear
                try:
                    academic_year = AcademicYear.objects.get(id=year_id, school_id=school_id)
                except AcademicYear.DoesNotExist:
                    academic_year = None
            
            from aid.models import AidApplication
            
            # Build query
            query = AidApplication.objects.filter(id__in=ids)
            if school_id:
                query = query.filter(school_id=school_id)
            
            apps = query.select_related("family").select_related("academic_year")
            apps_by_id = {str(a.id): a for a in apps}
            
            for raw_id in ids:
                app = apps_by_id.get(str(raw_id))
                if not app:
                    failures.append({
                        "id": str(raw_id),
                        "reason": "Application not found for school/year"
                    })
                    continue
                
                # Enforce NEEDS_INFO status
                if app.status != AidApplication.STATUS_NEEDS_INFO:
                    failures.append({
                        "id": str(app.id),
                        "reason": f"Application is in {app.status} status, not NEEDS_INFO"
                    })
                    continue
                
                family = getattr(app, "family", None)
                family_name = getattr(family, "family_name", "Family") if family else "Family"
                
                # Try to fetch missing documents
                missing = []
                try:
                    # Attempt to find missing documents
                    from aid.models import AidDocument
                    missing_qs = AidDocument.objects.filter(
                        aid_application=app,
                        received=False
                    ).order_by("doc_type")
                    for d in missing_qs:
                        label = getattr(d, "doc_label", None) or getattr(d, "doc_type", None) or "Document"
                        missing.append(str(label))
                except Exception:
                    # If AidDocument doesn't exist or different structure, use generic
                    missing = []
                
                missing_lines = "\n".join([f"- {m}" for m in missing]) if missing else "- One or more required documents (see your portal checklist)"
                
                subject = "Financial Aid Application – Additional Information Needed"
                
                ay_name = getattr(academic_year or app.academic_year, "name", "current school year")
                
                body = f"""Hello {family_name},

Thank you for submitting your financial aid application for the {ay_name}.

Before we can complete your review, we still need the following item(s):

{missing_lines}

What to do next:
1) Log into the Crown Family Portal
2) Open your Financial Aid Application
3) Upload the missing document(s) under "Documents"
4) Submit updates when finished

If you have questions, reply to this email and we will help you.

With appreciation,
Crown Financial Aid Office
"""
                
                drafts.append({
                    "application_id": str(app.id),
                    "family": family_name,
                    "subject": subject,
                    "body": body,
                })
            
            return Response({
                "action": action,
                "draft_count": len(drafts),
                "failure_count": len(failures),
                "drafts": drafts,
                "failures": failures if failures else None,
                "priority_refresh": build_director_priority_snapshot(school_id, academic_year),
            }, status=status.HTTP_200_OK)
        
        elif action == "AID_MARK_NEEDS_INFO_EMAIL_SENT":
            # Mark needs-info email sent + optionally move to under review
            from django.utils import timezone
            move_to_under_review = bool(payload.get("move_to_under_review", False))
            
            successes = []
            failures = []
            
            from aid.models import AidApplication
            
            query = AidApplication.objects.filter(id__in=ids)
            if school_id:
                query = query.filter(school_id=school_id)
            if year_id:
                query = query.filter(academic_year_id=year_id)
            
            apps = query.select_related("family")
            apps_by_id = {str(a.id): a for a in apps}
            
            now = timezone.now()
            
            for raw_id in ids:
                app = apps_by_id.get(str(raw_id))
                if not app:
                    failures.append({"id": str(raw_id), "reason": "Application not found for school/year"})
                    continue
                
                if app.status != AidApplication.STATUS_NEEDS_INFO:
                    failures.append({"id": str(app.id), "reason": f"Application is in {app.status} status, not NEEDS_INFO"})
                    continue
                
                # Update audit fields
                app.last_contacted_at = now
                app.last_contacted_by = request.user if getattr(request.user, "is_authenticated", False) else None
                app.last_contacted_reason = "NEEDS_INFO_EMAIL"
                
                # Optional: director can move it along after sending message
                if move_to_under_review:
                    app.status = AidApplication.STATUS_UNDER_REVIEW
                
                app.save(update_fields=[
                    "last_contacted_at",
                    "last_contacted_by",
                    "last_contacted_reason",
                    "status",
                ])
                
                successes.append({
                    "application_id": str(app.id),
                    "family": getattr(getattr(app, "family", None), "family_name", None),
                    "moved_to_under_review": move_to_under_review,
                    "last_contacted_at": app.last_contacted_at,
                })
            
            return Response({
                "action": action,
                "success_count": len(successes),
                "failure_count": len(failures),
                "successes": successes,
                "failures": failures if failures else None,
                "priority_refresh": build_director_priority_snapshot(school_id, academic_year),
            }, status=status.HTTP_200_OK)
        
        else:
            return Response(
                {"error": f"Unknown action: {action}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def director_timeline(request):
    """
    Unified audit-style timeline of recent director-relevant events.
    Tightened for director storytelling: high-impact events first,
    noisy GL entries suppressed.
    
    Params:
    - school_id: UUID of school
    - year_id (or academic_year_id): UUID of academic year
    - limit: max items to return (default 50)
    """
    if not crown_director_allowed(request):
        return Response(
            {"error": "Unauthorized. Director access required."},
            status=status.HTTP_403_FORBIDDEN,
        )
    
    school_id = request.query_params.get("school_id")
    year_id = request.query_params.get("year_id") or request.query_params.get("academic_year_id")
    limit = int(request.query_params.get("limit") or 50)
    
    academic_year = resolve_academic_year(school_id, year_id)
    
    if not academic_year:
        return Response(
            {"error": "Academic year not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
    
    items = []
    
    # --- Aid: Awards posted to ledger (director actions, high-impact) ---
    posted_awards = (
        AidAward.objects
        .filter(
            school_id=school_id,
            academic_year=academic_year,
            ledger_entry__isnull=False,
        )
        .select_related("student", "student__family", "ledger_entry")
        .order_by("-ledger_entry__created_at")[:limit]
    )
    
    for w in posted_awards:
        student = getattr(w, "student", None)
        student_name = (f"{getattr(student,'first_name','')} {getattr(student,'last_name','')}".strip() if student else "Student")
        le = getattr(w, "ledger_entry", None)
        
        # timestamp fallback chain
        ts = getattr(w, "posted_at", None) or getattr(le, "created_at", None) or getattr(le, "entry_date", None) or timezone.now()
        amt_cents = getattr(w, "awarded_cents", None)
        
        # Format amount as currency if present
        if amt_cents:
            amt_dollars = amt_cents / 100.0
            summary = f"${amt_dollars:,.0f} aid posted: {student_name}"
        else:
            summary = f"Aid posted: {student_name}"
        
        items.append({
            "ts": ts,
            "type": "AID_POSTED_TO_LEDGER",
            "actor": "Director Action" if getattr(w, "posted_by_id", None) else "System",
            "entity": "AidAward",
            "entity_id": str(w.id),
            "amount_cents": amt_cents,
            "summary": summary,
        })
    
    # --- Aid: Needs-info outreach contacts (non-routine contacts only) ---
    recent_contacts = (
        AidApplication.objects
        .filter(
            school_id=school_id,
            academic_year=academic_year,
            last_contacted_at__isnull=False,
        )
        .select_related("family", "last_contacted_by")
        .order_by("-last_contacted_at")[:limit]
    )
    
    for a in recent_contacts:
        actor = getattr(getattr(a, "last_contacted_by", None), "username", None) or "System"
        family_name = getattr(getattr(a, "family", None), "family_name", "Family")
        reason = getattr(a, "last_contacted_reason", None) or "Contacted"
        
        # Skip generic/routine contact reasons
        if reason.upper() in ["CONTACT", "ROUTINE"]:
            continue
        
        items.append({
            "ts": a.last_contacted_at,
            "type": "AID_CONTACT",
            "actor": actor,
            "entity": "AidApplication",
            "entity_id": str(a.id),
            "summary": f"{reason}: {family_name}",
        })
    
    # --- Finance: Significant ledger activity (payments, major charges, exclude routine GL) ---
    recent_ledger = (
        LedgerEntry.objects
        .filter(
            school_id=school_id,
            academic_year=academic_year,
        )
        .select_related("family", "student")
        .order_by("-created_at")[:limit * 2]  # Fetch more to filter
    )
    
    for le in recent_ledger:
        amt = getattr(le, "amount_cents", None)
        
        # Suppress zero-amount and routine GL entries
        if amt is None or amt == 0:
            continue
        
        acct = getattr(le, "account_code", None) or getattr(getattr(le, "account", None), "code", None) or "LEDGER"
        
        # Suppress routine GL codes (adjustments, temporary entries)
        if acct.upper() in ["GL_ADJUSTMENT", "TEMP", "PENDING"]:
            continue
        
        fam = getattr(le, "family", None)
        student = getattr(le, "student", None)
        family_name = getattr(fam, "family_name", None)
        student_name = (f"{getattr(student,'first_name','')} {getattr(student,'last_name','')}".strip() if student else None)
        
        ts = getattr(le, "created_at", None) or getattr(le, "entry_date", None) or timezone.now()
        who = family_name or student_name or "Account"
        
        # Tighten summary with amount
        amt_dollars = amt / 100.0
        sign = "+" if amt > 0 else "-"
        summary = f"{sign}${abs(amt_dollars):,.0f} {acct}: {who}"
        
        items.append({
            "ts": ts,
            "type": "LEDGER_ENTRY",
            "actor": "System",
            "entity": "LedgerEntry",
            "entity_id": str(le.id),
            "amount_cents": amt,
            "summary": summary,
        })
    
    # Sort by timestamp (reverse chrono), trim
    items = [i for i in items if i.get("ts") is not None]
    items.sort(key=lambda x: x["ts"], reverse=True)
    items = items[:limit]
    
    return Response({
        "meta": {
            "school_id": school_id,
            "year_id": year_id,
            "limit": limit,
            "count": len(items),
        },
        "timeline": items,
    }, status=status.HTTP_200_OK)


import os
import logging
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)

def _crown_env() -> str:
    crown_env = os.environ.get("CROWN_ENV") or getattr(settings, "CROWN_ENV", None)
    if crown_env:
        return str(crown_env).strip().lower()
    return "dev" if getattr(settings, "DEBUG", False) else "prod"


def _is_dev_env() -> bool:
    env = _crown_env()
    if env == "prod":
        # Absolute deny: never allow seeding behaviors in prod
        return False
    return env == "dev"


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])       # prevent DRF from requiring JWT automatically
def force_seed_user(request):
    """
    DEV-only emergency seeding endpoint.
    AuthZ: (JWT staff/superuser) OR (X-Dev-Seed-Key matches DEV_SEED_KEY).
    Never returns credentials.
    """
    if not _is_dev_env():
        # Hide existence outside DEV
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    # Authorization path A: authenticated staff/superuser
    user = getattr(request, "user", None)
    jwt_ok = bool(user and getattr(user, "is_authenticated", False) and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)))

    # Authorization path B: dev seed key
    provided = request.headers.get("X-Dev-Seed-Key") or request.headers.get("X-DEV-SEED-KEY")
    expected = os.environ.get("DEV_SEED_KEY") or getattr(settings, "DEV_SEED_KEY", None)
    key_ok = bool(expected and provided and provided == expected)

    if not (jwt_ok or key_ok):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    try:
        from django.core.management import call_command
        from django.core.management.base import CommandError
        
        # Run migrations
        call_command('migrate', verbosity=1)
        
        # Run dev_bootstrap to create admin user
        admin_password = os.environ.get("DEV_ADMIN_PASSWORD", "Crown2026!")
        call_command('dev_bootstrap', admin_password=admin_password, verbosity=1)
        
        logger.warning(
            "DEV_SEED invoked: actor=%s auth=%s",
            getattr(user, "username", None) if jwt_ok else None,
            "jwt" if jwt_ok else "seed_key"
        )

        return Response(
            {
                "ok": True,
                "message": "Seed operation completed (details suppressed).",
                "already_seeded": False,   # or True if you detect it
            },
            status=status.HTTP_200_OK
        )
    except CommandError as e:
        logger.exception("DEV_SEED failed: %s", str(e))
        return Response(
            {"ok": False, "message": "Seed operation failed."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )