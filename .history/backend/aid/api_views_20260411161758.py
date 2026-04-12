"""
Persona-specific API views for Aid Director

Each director persona gets isolated APIs that return ONLY their data.
Contract must be identical across all director personas.
"""

import logging

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum

from aid.models import AidApplication, AidAward, AidPolicy, AidBudgetTracker
from aid.serializers import (
    AidApplicationSerializer,
    AidAwardSerializer,
    AidAwardWithExplanationSerializer,
    AidBudgetTrackerSerializer,
)
from aid.services.award_engine import recommend_award
from aid.services.ledger_bridge import AidBudgetError, approve_award
from core.models import AcademicYear, LedgerEntry
from households.scoping import MissingSchoolContext, get_request_school_id


logger = logging.getLogger(__name__)


def days_waiting(dt):
    """Calculate days since timestamp"""
    if not dt:
        return 0
    now = timezone.now()
    delta = now - dt
    return max(0, int(delta.total_seconds() // 86400))


@extend_schema(
    operation_id="aid_priority_queue",
    tags=["Aid"],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def aid_priority_queue(request):
    """
    Priority queue for Aid Director - returns ONLY aid-related items.

    Contract: All director priority-queue APIs must return:
    {
        "rows": [{"type", "score", "id", "summary", "timestamp", ...}],
        "meta": {"persona", "count"}
    }
    """
    # Get context (in production, from session/auth)
    school_id = request.query_params.get('school_id')
    year_id = request.query_params.get('year_id')

    if not school_id or not year_id:
        return Response(
            {"detail": "school_id and year_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Query aid applications
    needs_info_apps = (
        AidApplication.objects
        .filter(school_id=school_id, academic_year_id=year_id,
                status=AidApplication.STATUS_NEEDS_INFO)
        .select_related("family")
        .order_by("-submitted_at")[:20]
    )

    under_review_apps = (
        AidApplication.objects
        .filter(school_id=school_id, academic_year_id=year_id,
                status=AidApplication.STATUS_UNDER_REVIEW)
        .select_related("family")
        .order_by("-submitted_at")[:20]
    )

    accepted_awards = (
        AidAward.objects
        .filter(school_id=school_id, academic_year_id=year_id,
                decision_status=AidAward.DECISION_ACCEPTED,
                ledger_entry__isnull=True)
        .select_related("student", "student__family")
        .order_by("-decided_at", "-created_at")[:20]
    )

    # Build scored rows
    rows = []

    for app in needs_info_apps:
        score = 100 + (days_waiting(app.submitted_at) * 3)
        rows.append({
            "type": "AID_APPLICATION_NEEDS_INFO",
            "score": score,
            "id": str(app.id),
            "family": getattr(app.family, "family_name", None),
            "timestamp": app.submitted_at.isoformat() if app.submitted_at else None,
            "summary": "Application needs info (missing documents).",
        })

    for app in under_review_apps:
        score = 60 + (days_waiting(app.submitted_at) * 2)
        rows.append({
            "type": "AID_APPLICATION_UNDER_REVIEW",
            "score": score,
            "id": str(app.id),
            "family": getattr(app.family, "family_name", None),
            "timestamp": app.submitted_at.isoformat() if app.submitted_at else None,
            "summary": "Application under review.",
        })

    for award in accepted_awards:
        award_dollars = (award.awarded_cents or 0) / 100
        score = 90 + min(40, int(award_dollars // 500))
        rows.append({
            "type": "AID_AWARD_ACCEPTED_NOT_POSTED",
            "score": score,
            "id": str(award.id),
            "student": f"{award.student.first_name} {award.student.last_name}" if award.student else None,
            "family": getattr(getattr(award.student, "family", None), "family_name", None),
            "timestamp": award.decided_at.isoformat() if award.decided_at else None,
            "summary": "Accepted award not posted to ledger.",
            "awarded_cents": award.awarded_cents,
        })

    # Sort by score descending
    rows.sort(key=lambda x: x["score"], reverse=True)

    return Response({
        "rows": rows,
        "meta": {
            "persona": "aid",
            "count": len(rows),
        }
    })


@extend_schema(
    operation_id="aid_metrics",
    tags=["Aid"],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def aid_metrics(request):
    """
    Metrics for Aid Director - returns ONLY aid metrics.

    Contract: All director metrics APIs must return:
    {
        "metrics": {"key": value, ...},
        "meta": {"persona"}
    }
    """
    school_id = request.query_params.get('school_id')
    year_id = request.query_params.get('year_id')

    if not school_id or not year_id:
        return Response(
            {"detail": "school_id and year_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Count applications by status
    total_applications = AidApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id
    ).count()

    needs_info_count = AidApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AidApplication.STATUS_NEEDS_INFO
    ).count()

    under_review_count = AidApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AidApplication.STATUS_UNDER_REVIEW
    ).count()

    accepted_count = AidApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AidApplication.STATUS_APPROVED
    ).count()

    # Sum total awarded
    total_awarded = AidAward.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        decision_status=AidAward.DECISION_ACCEPTED
    ).aggregate(total=Sum('awarded_cents'))['total'] or 0

    return Response({
        "metrics": {
            "applications_count": total_applications,
            "needs_info_count": needs_info_count,
            "under_review_count": under_review_count,
            "accepted_count": accepted_count,
            "total_awarded_cents": total_awarded,
        },
        "meta": {
            "persona": "aid",
        }
    })


@extend_schema(
    operation_id="aid_timeline",
    tags=["Aid"],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def aid_timeline(request):
    """
    Timeline for Aid Director - returns ONLY aid events.

    Contract: All director timeline APIs must return:
    {
        "events": [{"timestamp", "type", "actor", "summary", "id"}],
        "meta": {"persona", "count"}
    }
    """
    school_id = request.query_params.get('school_id')
    year_id = request.query_params.get('year_id')

    if not school_id or not year_id:
        return Response(
            {"detail": "school_id and year_id are required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get recent aid applications
    recent_apps = (
        AidApplication.objects
        .filter(school_id=school_id, academic_year_id=year_id)
        .select_related("family")
        .order_by("-submitted_at")[:50]
    )

    events = []
    for app in recent_apps:
        events.append({
            "timestamp": app.submitted_at.isoformat() if app.submitted_at else None,
            "type": "AID_APPLICATION_SUBMITTED",
            "actor": None,  # AidApplication doesn't have submitted_by field
            "summary": f"Application submitted by {getattr(app.family, 'family_name', 'Unknown')} family",
            "id": str(app.id),
        })

    # Sort by timestamp descending
    events.sort(key=lambda x: x["timestamp"], reverse=True)

    return Response({
        "events": events[:50],  # Limit to 50
        "meta": {
            "persona": "aid",
            "count": len(events[:50]),
        }
    })


# ---------------------------------------------------------------------------
# Phase 7.5: Admin + Family endpoints
# ---------------------------------------------------------------------------

@extend_schema(
    operation_id="admin_aid_overview",
    tags=["Aid"],
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admin_aid_overview(request):
    """
    Admin overview: applications + awards + budgets for a school/year.

    Required query params: academic_year_id (integer PK of AcademicYear)
    Required header:       X-School-Id (tenant UUID)
    """
    school_id = get_request_school_id(request)
    academic_year_id = request.query_params.get("academic_year_id")
    if not academic_year_id:
        return Response({"detail": "academic_year_id is required"}, status=status.HTTP_400_BAD_REQUEST)

    applications = (
        AidApplication.objects.filter(school_id=school_id, academic_year_id=academic_year_id)
        .order_by("-submitted_at")
    )
    awards = (
        AidAward.objects.filter(school_id=school_id, academic_year_id=academic_year_id)
        .order_by("-created_at")
    )
    budgets = (
        AidBudgetTracker.objects.filter(school_id=school_id, academic_year_id=academic_year_id)
        .order_by("bucket")
    )

    return Response({
        "applications": AidApplicationSerializer(applications, many=True).data,
        "awards": AidAwardSerializer(awards, many=True).data,
        "budgets": AidBudgetTrackerSerializer(budgets, many=True).data,
    })


@extend_schema(
    operation_id="admin_recommend_award",
    tags=["Aid"],
    request=OpenApiTypes.OBJECT,
    responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_recommend_award(request):
    """
    Generate a new award recommendation via the award engine.

    Required body fields:
      application_id      (int PK of AidApplication to evaluate)
      bucket              (award_type: NEED|MISSION|MERIT|HARDSHIP|MARKETING)
      gross_tuition_cents (int, gross tuition for this student/year)

    Required header: X-School-Id

    Creates and returns an AidAward in status OFFERED with engine outputs stored.
    """
    school_id = get_request_school_id(request)

    application_id = request.data.get("application_id")
    bucket = request.data.get("bucket")
    gross_tuition_cents_raw = request.data.get("gross_tuition_cents")

    if not application_id or not bucket or gross_tuition_cents_raw is None:
        return Response(
            {"detail": "application_id, bucket, and gross_tuition_cents are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        gross_tuition_cents = int(gross_tuition_cents_raw)
    except (TypeError, ValueError):
        return Response({"detail": "gross_tuition_cents must be an integer"}, status=status.HTTP_400_BAD_REQUEST)

    if gross_tuition_cents <= 0:
        return Response({"detail": "gross_tuition_cents must be > 0"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        app = AidApplication.objects.get(pk=application_id, school_id=school_id)
    except (AidApplication.DoesNotExist, ValueError, TypeError):
        return Response({"detail": "AidApplication not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        policy = AidPolicy.objects.get(school_id=school_id, academic_year=app.academic_year)
    except AidPolicy.DoesNotExist:
        return Response(
            {"detail": "No AidPolicy found for this school and academic year"},
            status=status.HTTP_404_NOT_FOUND,
        )

    rec = recommend_award(policy, app, gross_tuition_cents)

    award = AidAward.objects.create(
        school=app.school,
        academic_year=app.academic_year,
        student=app.family.students.first(),  # one student per application (common case)
        aid_application=app,
        award_type=bucket,
        awarded_cents=rec.recommended_award_cents,
        recommended_award_cents=rec.recommended_award_cents,
        mas_score=rec.mas_score,
        mas_modifier_bps=rec.mas_modifier_bps,
        explanation_json=rec.explanation,
        decision_status=AidAward.DECISION_OFFERED,
    )

    return Response(
        {
            "award": AidAwardWithExplanationSerializer(award).data,
            "explanation": rec.explanation,
        },
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    operation_id="admin_approve_award",
    tags=["Aid"],
    request=OpenApiTypes.OBJECT,
    responses={200: AidAwardSerializer, 404: OpenApiTypes.OBJECT, 409: OpenApiTypes.OBJECT},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admin_approve_award(request, award_id):
    """
    Approve an AidAward: budget check → ledger posting → audit log.

    URL param: award_id (int PK)
    Optional body: {"reason": "..."}
    Required header: X-School-Id

    Idempotent: approving an already-accepted award is a no-op (returns 200).
    409 if bucket budget would be exceeded.
    """
    school_id = get_request_school_id(request)
    reason = request.data.get("reason", "")

    try:
        award = AidAward.objects.get(pk=award_id, school_id=school_id)
    except AidAward.DoesNotExist:
        return Response({"detail": "Award not found"}, status=status.HTTP_404_NOT_FOUND)

    try:
        approved = approve_award(
            award=award,
            actor_user=request.user if request.user.is_authenticated else None,
            reason=reason,
        )
    except AidBudgetError:
        logger.warning("admin_approve_award: budget conflict while approving award", extra={"award_id": award_id})
        return Response({"error": "Unable to approve award due to budget constraints."}, status=status.HTTP_409_CONFLICT)
    except AidBudgetTracker.DoesNotExist:
        return Response(
            {"error": "No budget tracker found for this bucket. Create one before approving."},
            status=status.HTTP_409_CONFLICT,
        )

    return Response(AidAwardSerializer(approved).data)


@extend_schema(
    operation_id="family_aid_status",
    tags=["Aid"],
    responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def family_aid_status(request):
    """
    Family-portal view: application status + awards for a student/year.

    Required query params:
      student_id       (int PK of Student)
      academic_year_id (int PK of AcademicYear)
    Required header: X-School-Id
    """
    school_id = get_request_school_id(request)
    student_id = request.query_params.get("student_id")
    academic_year_id = request.query_params.get("academic_year_id")

    if not student_id or not academic_year_id:
        return Response(
            {"detail": "student_id and academic_year_id are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Application is tied to the family, not the student — look up via student.family
    from core.models import Student  # local import to avoid circular at module level
    try:
        student = Student.objects.get(pk=student_id, school_id=school_id)
    except Student.DoesNotExist:
        return Response({"detail": "Student not found"}, status=status.HTTP_404_NOT_FOUND)

    application = AidApplication.objects.filter(
        school_id=school_id,
        family=student.family,
        academic_year_id=academic_year_id,
    ).first()

    awards = AidAward.objects.filter(
        school_id=school_id,
        student=student,
        academic_year_id=academic_year_id,
    ).order_by("-created_at")

    return Response({
        "application": AidApplicationSerializer(application).data if application else None,
        "awards": AidAwardSerializer(awards, many=True).data,
    })
