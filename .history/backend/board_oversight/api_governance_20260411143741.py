"""
board_oversight/api_governance.py

Stage 4 board governance API endpoints:

  GET  /api/v1/board/packet/download/     — PDF board packet download
  GET  /api/v1/board/compass/             — Crown Compass executive summary
  GET  /api/v1/board/initiatives/         — strategic initiative summary
  GET  /api/v1/board/trends/              — KPI trend data
  GET  /api/v1/board/roadmap/             — public roadmap items
  GET  /api/v1/board/releases/            — versioned release notes
"""
from django.http import HttpResponse, JsonResponse
from drf_spectacular.utils import OpenApiResponse, OpenApiTypes, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from board_oversight.models_governance import (
    StrategicInitiative,
    BoardKPISnapshot,
    RoadmapItem,
    ReleaseLog,
)
from board_oversight.services_pdf import generate_board_packet
from board_oversight.tenant import require_school_id


BOARD_COMPASS_RESPONSE = inline_serializer(
    name="BoardCompassExecutiveResponse",
    fields={
        "school_id": serializers.CharField(allow_null=True),
        "enrollment_health": serializers.IntegerField(),
        "financial_health": serializers.IntegerField(),
        "discipline_health": serializers.IntegerField(),
        "spiritual_life_health": serializers.IntegerField(),
        "overall_score": serializers.IntegerField(),
    },
)

BOARD_INITIATIVE_RESPONSE = inline_serializer(
    name="BoardInitiativeSummaryResponse",
    fields={
        "school_id": serializers.CharField(),
        "total_initiatives": serializers.IntegerField(),
        "completed": serializers.IntegerField(),
        "completion_rate": serializers.FloatField(),
        "initiatives": serializers.ListField(child=serializers.DictField()),
    },
)

BOARD_TRENDS_RESPONSE = inline_serializer(
    name="BoardTrendsResponse",
    fields={
        "school_id": serializers.CharField(),
        "trends": serializers.ListField(child=serializers.DictField()),
    },
)

BOARD_ROADMAP_RESPONSE = inline_serializer(
    name="BoardRoadmapResponse",
    fields={
        "roadmap": serializers.ListField(child=serializers.DictField()),
    },
)

BOARD_RELEASE_NOTES_RESPONSE = inline_serializer(
    name="BoardReleaseNotesResponse",
    fields={
        "releases": serializers.ListField(child=serializers.DictField()),
    },
)


# ── PDF Board Packet ───────────────────────────────────────────────────────

@extend_schema(
    tags=["Board Oversight"],
    responses={
        (200, "application/pdf"): OpenApiTypes.BINARY,
        503: OpenApiResponse(description="PDF generation unavailable."),
    },
)
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


# ── Crown Compass ──────────────────────────────────────────────────────────

def _compass_summary(school_id=None) -> dict:
    """
    Aggregate high-level board summary values across pillars.
    Placeholder values remain in use until governed data pipelines are explicitly approved.
    This helper should not be treated as Crown Discernment production integration.
    """
    # TODO: derive from real BoardKPISnapshot rows when available
    return {
        "school_id": str(school_id) if school_id else None,
        "enrollment_health": 92,
        "financial_health": 88,
        "discipline_health": 95,
        "spiritual_life_health": 90,
        "overall_score": 91,
    }


@extend_schema(tags=["Board Oversight"], responses=BOARD_COMPASS_RESPONSE)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def compass_executive(request):
    """Current Crown Compass executive summary surface using stored / placeholder board metrics."""
    school_id = require_school_id(request)
    return Response(_compass_summary(school_id=school_id))


# ── Strategic Initiatives ─────────────────────────────────────────────────

@extend_schema(tags=["Board Oversight"], responses=BOARD_INITIATIVE_RESPONSE)
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


# ── KPI Trends ────────────────────────────────────────────────────────────

@extend_schema(tags=["Board Oversight"], responses=BOARD_TRENDS_RESPONSE)
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


# ── Public Roadmap ────────────────────────────────────────────────────────

@extend_schema(tags=["Board Oversight"], responses=BOARD_ROADMAP_RESPONSE)
@api_view(["GET"])
@permission_classes([AllowAny])
def public_roadmap(request):
    """Public-facing product roadmap — no auth required."""
    items = list(RoadmapItem.objects.filter(status__in=["planned", "in_progress", "released"])
                 .values("title", "description", "status", "target_release"))
    return Response({"roadmap": items})


# ── Release Notes ──────────────────────────────────────────────────────────

@extend_schema(tags=["Board Oversight"], responses=BOARD_RELEASE_NOTES_RESPONSE)
@api_view(["GET"])
@permission_classes([AllowAny])
def release_notes(request):
    """Versioned release log — public."""
    logs = list(ReleaseLog.objects.values("version", "release_date", "notes"))
    return Response({"releases": logs})
