"""
Persona-specific API views for Admissions Director

Each director persona gets isolated APIs that return ONLY their data.
Contract must be identical across all director personas.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from admissions.models import AdmissionsApplication


def days_waiting(dt):
    """Calculate days since timestamp"""
    if not dt:
        return 0
    now = timezone.now()
    delta = now - dt
    return max(0, int(delta.total_seconds() // 86400))


@api_view(["GET"])
@permission_classes([AllowAny])
def admissions_priority_queue(request):
    """
    Priority queue for Admissions Director - returns ONLY admissions-related items.
    
    Contract: All director priority-queue APIs must return:
    {
        "rows": [{"type", "score", "id", "summary", "timestamp", ...}],
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
    
    # Query admissions applications
    needs_info_apps = (
        AdmissionsApplication.objects
        .filter(school_id=school_id, academic_year_id=year_id,
                status=AdmissionsApplication.STATUS_NEEDS_INFO)
        .select_related("family")
        .order_by("-submitted_at")[:20]
    )
    
    under_review_apps = (
        AdmissionsApplication.objects
        .filter(school_id=school_id, academic_year_id=year_id,
                status=AdmissionsApplication.STATUS_UNDER_REVIEW)
        .select_related("family")
        .order_by("-submitted_at")[:20]
    )
    
    # Build scored rows
    rows = []
    
    for app in needs_info_apps:
        score = 100 + (days_waiting(app.submitted_at) * 3)
        rows.append({
            "type": "ADMISSIONS_APPLICATION_NEEDS_INFO",
            "score": score,
            "id": str(app.id),
            "family": getattr(app.family, "family_name", None),
            "timestamp": app.submitted_at.isoformat() if app.submitted_at else None,
            "summary": "Admissions application needs info (missing documents).",
        })
    
    for app in under_review_apps:
        score = 60 + (days_waiting(app.submitted_at) * 2)
        rows.append({
            "type": "ADMISSIONS_APPLICATION_UNDER_REVIEW",
            "score": score,
            "id": str(app.id),
            "family": getattr(app.family, "family_name", None),
            "timestamp": app.submitted_at.isoformat() if app.submitted_at else None,
            "summary": "Admissions application under review.",
        })
    
    # Sort by score descending
    rows.sort(key=lambda x: x["score"], reverse=True)
    
    return Response({
        "rows": rows,
        "meta": {
            "persona": "admissions",
            "count": len(rows),
        }
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def admissions_metrics(request):
    """
    Metrics for Admissions Director - returns ONLY admissions metrics.
    
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
    total_applications = AdmissionsApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id
    ).count()
    
    needs_info_count = AdmissionsApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AdmissionsApplication.STATUS_NEEDS_INFO
    ).count()
    
    under_review_count = AdmissionsApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AdmissionsApplication.STATUS_UNDER_REVIEW
    ).count()
    
    accepted_count = AdmissionsApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AdmissionsApplication.STATUS_ACCEPTED
    ).count()
    
    waitlisted_count = AdmissionsApplication.objects.filter(
        school_id=school_id, academic_year_id=year_id,
        status=AdmissionsApplication.STATUS_WAITLISTED
    ).count()
    
    return Response({
        "metrics": {
            "applications_count": total_applications,
            "needs_info_count": needs_info_count,
            "under_review_count": under_review_count,
            "accepted_count": accepted_count,
            "waitlisted_count": waitlisted_count,
        },
        "meta": {
            "persona": "admissions",
        }
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def admissions_timeline(request):
    """
    Timeline for Admissions Director - returns ONLY admissions events.
    
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
    
    # Get recent admissions applications
    recent_apps = (
        AdmissionsApplication.objects
        .filter(school_id=school_id, academic_year_id=year_id)
        .select_related("family", "submitted_by")
        .order_by("-submitted_at")[:50]
    )
    
    events = []
    for app in recent_apps:
        events.append({
            "timestamp": app.submitted_at.isoformat() if app.submitted_at else None,
            "type": "ADMISSIONS_APPLICATION_SUBMITTED",
            "actor": app.submitted_by.email if app.submitted_by else None,
            "summary": f"Application submitted by {getattr(app.family, 'family_name', 'Unknown')} family",
            "id": str(app.id),
        })
    
    # Sort by timestamp descending
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return Response({
        "events": events[:50],  # Limit to 50
        "meta": {
            "persona": "admissions",
            "count": len(events[:50]),
        }
    })
