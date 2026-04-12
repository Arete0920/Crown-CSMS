from __future__ import annotations

from datetime import date

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from board_oversight.models import BoardPacket
from board_oversight.tenant import require_school_id
from core.permissions import user_has_permission
from governance.scheduler import build_schedule_status, run_scheduled_board_pack_job
from governance.openapi import (
    board_metrics_schema,
    board_pack_detail_schema,
    board_packs_get_schema,
    board_packs_post_schema,
    crown_compass_history_schema,
    crown_compass_schema,
    governance_dashboard_schema,
    governance_schedule_get_schema,
    governance_schedule_post_schema,
    heritage_governance_verification_schema,
)
from governance.services import (
    build_board_dashboard_payload,
    build_board_metrics_payload,
    build_heritage_verification_payload,
    create_board_packet_from_live_data,
    list_crown_compass_history,
    refresh_crown_compass_metric,
    serialize_board_packet,
)


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _check_board_access(request):
    school = getattr(request, "school", None)
    if not user_has_permission(request.user, "board.view", school=school):
        return None, Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)
    return require_school_id(request), None


@board_metrics_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def governance_board_metrics(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    return Response(build_board_metrics_payload(school_id=school_id))


@governance_dashboard_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def governance_dashboard(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    return Response(build_board_dashboard_payload(school_id=school_id))


@crown_compass_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def crown_compass(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    return Response(refresh_crown_compass_metric(school_id))


@crown_compass_history_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def crown_compass_history(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    limit = request.query_params.get("limit")
    try:
        parsed_limit = int(limit) if limit else 12
    except ValueError:
        parsed_limit = 12
    parsed_limit = max(1, min(parsed_limit, 24))
    history = list_crown_compass_history(school_id, limit=parsed_limit)
    return Response({"results": history, "history": history, "source": "live_db"})


@board_packs_get_schema
@board_packs_post_schema
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def board_packs(request):
    school_id, err = _check_board_access(request)
    if err:
        return err

    if request.method == "GET":
        packets = BoardPacket.objects.filter(school_id=school_id).order_by("-meeting_date", "-created_at")[:20]
        return Response([serialize_board_packet(packet) for packet in packets])

    meeting_date = _parse_date(request.data.get("meeting_date")) or date.today()
    title = request.data.get("title") or None
    payload = create_board_packet_from_live_data(school_id, meeting_date=meeting_date, title=title)
    return Response(payload, status=status.HTTP_201_CREATED)


@board_pack_detail_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def board_pack_detail(request, packet_id: int):
    school_id, err = _check_board_access(request)
    if err:
        return err
    try:
        packet = BoardPacket.objects.get(pk=packet_id, school_id=school_id)
    except BoardPacket.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(serialize_board_packet(packet))


@governance_schedule_get_schema
@governance_schedule_post_schema
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def governance_schedule(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    if request.method == "GET":
        return Response(build_schedule_status(school_id))

    meeting_date = _parse_date(request.data.get("meeting_date"))
    title = request.data.get("title") or None
    return Response(
        run_scheduled_board_pack_job(school_id, meeting_date=meeting_date, title=title),
        status=status.HTTP_201_CREATED,
    )


@heritage_governance_verification_schema
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def heritage_governance_verification(request):
    school_id, err = _check_board_access(request)
    if err:
        return err
    return Response(build_heritage_verification_payload(school_id))
