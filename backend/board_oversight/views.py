from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from core.permissions import user_has_permission
from .models import BoardPacket, BoardReportSnapshot
from .serializers import BoardPacketSerializer, BoardReportSnapshotSerializer
from .tenant import require_school_id
from .services import build_board_metrics_payload, build_board_dashboard_payload


def _check_board_access(request):
    """Return (school_id, error_response) tuple. error_response is None if OK."""
    school = getattr(request, "school", None)
    if not user_has_permission(request.user, "board.view", school=school):
        return None, Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
    school_id = require_school_id(request)
    return school_id, None


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def board_metrics(request):
    """Primary endpoint consumed by the existing BoardDashboard frontend.
    Returns aggregated board-safe KPIs in the shape the UI expects."""
    school_id, err = _check_board_access(request)
    if err:
        return err
    payload = build_board_metrics_payload(school_id=school_id)
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def board_dashboard(request):
    """Structured dashboard payload (spec-aligned, finer metric breakdown)."""
    school_id, err = _check_board_access(request)
    if err:
        return err
    payload = build_board_dashboard_payload(school_id=school_id)
    return Response(payload, status=status.HTTP_200_OK)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_snapshots(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    qs = BoardReportSnapshot.objects.filter(
        school_id=school_id
    ).order_by("-as_of_date", "-created_at")[:50]
    return Response(BoardReportSnapshotSerializer(qs, many=True).data, status=status.HTTP_200_OK)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_packets(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    qs = BoardPacket.objects.filter(
        school_id=school_id
    ).order_by("-meeting_date", "-created_at")[:50]
    return Response(BoardPacketSerializer(qs, many=True).data, status=status.HTTP_200_OK)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_packet(request, packet_id: int):
    school_id, err = _check_board_access(request)
    if err:
        return err
    try:
        pkt = BoardPacket.objects.get(pk=packet_id, school_id=school_id)
    except BoardPacket.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(BoardPacketSerializer(pkt).data, status=status.HTTP_200_OK)
