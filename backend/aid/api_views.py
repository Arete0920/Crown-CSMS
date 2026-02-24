"""
Persona-specific API views for Aid Director

Each director persona gets isolated APIs that return ONLY their data.
Contract must be identical across all director personas.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import Sum

from aid.models import AidApplication, AidAward
from core.models import AcademicYear, LedgerEntry


def days_waiting(dt):
    """Calculate days since timestamp"""
    if not dt:
        return 0
    now = timezone.now()
    delta = now - dt
    return max(0, int(delta.total_seconds() // 86400))


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
