"""
board_oversight/api_governance.py

Stage 4 board governance API endpoints:

  GET  /api/v1/board/packet/download/     - PDF board packet download
  GET  /api/v1/board/compass/             - Crown Compass executive summary
  GET  /api/v1/board/initiatives/         - strategic initiative summary
  GET  /api/v1/board/trends/              - KPI trend data
  GET  /api/v1/board/roadmap/             - public roadmap items
  GET  /api/v1/board/releases/            - versioned release notes
"""
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from board_oversight.models_governance import (
    StrategicInitiative,
    BoardKPISnapshot,
    RoadmapItem,
    ReleaseLog,
)
from board_oversight.services_pdf import generate_board_packet
from board_oversight.tenant import require_school_id


# PDF Board Packet

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_board_packet(request):
    """Generate and stream a PDF board packet for the caller's school."""
    school_id = require_school_id(request)
    pdf_buffer = generate_board_packet(school_id=school_id)
    if pdf_buffer is None:
        return Response(
            {"detail": "PDF generation unavailable. Install reportlab to enable this feature."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    response = HttpResponse(pdf_buffer.read(), content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=crown_board_packet.pdf"
    return response


# Crown Compass

def _compass_summary(school_id=None) -> dict:
    """Aggregate health scores across pillars from latest KPI snapshot."""
    school_label = str(school_id) if school_id else None
    latest = (
        BoardKPISnapshot.objects.filter(school_id=school_id).order_by("-month").first()
        if school_id
        else BoardKPISnapshot.objects.order_by("-month").first()
    )

    if latest is None:
        return {
            "school_id": school_label,
            "enrollment_health": 0,
            "financial_health": 0,
            "discipline_health": 0,
            "spiritual_life_health": 0,
            "overall_score": 0,
            "source": "empty",
        }

    enrollment_health = max(0, min(100, latest.enrollment))
    financial_health = max(0, min(100, int(float(latest.revenue) / 1000)))
    discipline_health = max(0, min(100, 100 - min(latest.discipline_incidents * 2, 100)))
    spiritual_health = max(0, min(100, latest.financial_aid_awards))
    overall = round((enrollment_health + financial_health + discipline_health + spiritual_health) / 4)

    return {
        "school_id": school_label,
        "enrollment_health": enrollment_health,
        "financial_health": financial_health,
        "discipline_health": discipline_health,
        "spiritual_life_health": spiritual_health,
        "overall_score": overall,
        "source": str(latest.month),
    }


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def compass_executive(request):
    """Crown Compass executive summary - overall institutional health scores."""
    school_id = require_school_id(request)
    return Response(_compass_summary(school_id=school_id))


# Strategic Initiatives

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def initiative_summary(request):
    """Strategic initiative completion rate for the caller's school."""
    school_id = require_school_id(request)
    qs = StrategicInitiative.objects.filter(school_id=school_id)
    total = qs.count()
    completed = qs.filter(status="complete").count()
    items = list(qs.values(
        "id", "title", "status", "owner_role", "target_date",
        "progress_percent", "created_at",
    ))
    return Response({
        "school_id": str(school_id),
        "total_initiatives": total,
        "completed": completed,
        "completion_rate": round((completed / total) * 100 if total else 0, 2),
        "initiatives": items,
    })


# KPI Trends

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def board_trends(request):
    """Monthly KPI trend snapshots for the caller's school."""
    school_id = require_school_id(request)
    data = list(
        BoardKPISnapshot.objects.filter(school_id=school_id)
        .values("month", "revenue", "enrollment", "discipline_incidents", "financial_aid_awards")
        .order_by("month")
    )
    return Response({"school_id": str(school_id), "trends": data})


# Public Roadmap

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_roadmap(request):
    """Public-facing product roadmap - no auth required."""
    items = list(RoadmapItem.objects.filter(status__in=["planned", "in_progress", "released"])
                 .values("title", "description", "status", "target_release"))
    return Response({"roadmap": items})


# Release Notes

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([AllowAny])
def release_notes(request):
    """Versioned release log - public."""
    logs = list(ReleaseLog.objects.values("version", "release_date", "notes"))
    return Response({"releases": logs})

