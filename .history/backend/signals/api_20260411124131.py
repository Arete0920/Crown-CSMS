from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer

from .tenant import school_id_from_request
from .models import (
    StudentRiskSnapshot,
    SignalEvent,
    InterventionCase,
    InterventionAction,
    BoardExecutiveMetric,
)
from .serializers import (
    StudentRiskSnapshotSerializer,
    SignalEventSerializer,
    InterventionCaseSerializer,
    InterventionActionSerializer,
    BoardExecutiveMetricSerializer,
)

SIGNALS_SCHOOL_HEADER = OpenApiParameter(
    name="X-School-Id",
    type=str,
    location=OpenApiParameter.HEADER,
    required=True,
    description="Tenant school scope header required for signals and intervention endpoints.",
)

BOARD_RISK_COUNTS_RESPONSE = inline_serializer(
    name="BoardRiskCountsResponse",
    fields={
        "as_of_date": serializers.CharField(allow_null=True),
        "low": serializers.IntegerField(),
        "med": serializers.IntegerField(),
        "high": serializers.IntegerField(),
    },
)

STUDENT_SIGNALS_RESPONSE = inline_serializer(
    name="StudentSignalsResponse",
    fields={
        "snapshot": StudentRiskSnapshotSerializer(allow_null=True),
        "events": SignalEventSerializer(many=True),
    },
)

INTERVENTION_CASE_CREATE_REQUEST = inline_serializer(
    name="InterventionCaseCreateRequest",
    fields={
        "student_id": serializers.UUIDField(),
        "reason": serializers.CharField(required=False),
        "priority": serializers.CharField(required=False),
        "linked_signals": serializers.ListField(child=serializers.JSONField(), required=False),
        "owner_user_id": serializers.IntegerField(required=False),
    },
)

INTERVENTION_ACTION_CREATE_REQUEST = inline_serializer(
    name="InterventionActionCreateRequest",
    fields={
        "action_type": serializers.CharField(required=False),
        "note": serializers.CharField(required=False, allow_blank=True),
        "created_by_user_id": serializers.IntegerField(required=False),
    },
)


# ---------------------------------------------------------------------------
# Board read-only endpoints
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Signals"],
    summary="Get board Compass summary",
    description="Returns the current stored board-facing Compass summary for the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    responses={200: BoardExecutiveMetricSerializer, 404: inline_serializer(name="SignalsNotFoundResponse", fields={"detail": serializers.CharField()})},
)
@api_view(["GET"])
def board_compass_summary(request):
    """Current stored Crown Compass summary surface; Discernment-style predictive insight remains hold-gated unless explicitly approved."""
    school_id = school_id_from_request(request, required=True)
    latest = (
        BoardExecutiveMetric.objects
        .filter(school_id=school_id)
        .order_by("-as_of_date")
        .first()
    )
    if not latest:
        return Response({"detail": "No metrics yet."}, status=status.HTTP_404_NOT_FOUND)
    return Response(BoardExecutiveMetricSerializer(latest).data)


@extend_schema(
    tags=["Signals"],
    summary="Get board risk counts",
    description="Returns LOW/MED/HIGH student risk counts for the latest snapshot date for the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    responses=BOARD_RISK_COUNTS_RESPONSE,
)
@api_view(["GET"])
def board_risk_counts(request):
    """Count of LOW/MED/HIGH risk students based on the most recent snapshot."""
    school_id = school_id_from_request(request, required=True)
    latest_date = (
        StudentRiskSnapshot.objects
        .filter(school_id=school_id)
        .order_by("-as_of_date")
        .values_list("as_of_date", flat=True)
        .first()
    )
    if not latest_date:
        return Response({"low": 0, "med": 0, "high": 0, "as_of_date": None})

    qs = StudentRiskSnapshot.objects.filter(school_id=school_id, as_of_date=latest_date)
    return Response({
        "as_of_date": str(latest_date),
        "low":  qs.filter(risk_level="LOW").count(),
        "med":  qs.filter(risk_level="MED").count(),
        "high": qs.filter(risk_level="HIGH").count(),
    })


# ---------------------------------------------------------------------------
# Staff-facing endpoints
# ---------------------------------------------------------------------------

@extend_schema(
    tags=["Signals"],
    summary="Get student signals",
    description="Returns the latest risk snapshot and recent signal events for one student in the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    responses=STUDENT_SIGNALS_RESPONSE,
)
@api_view(["GET"])
def student_signals(request, student_id):
    """Per-student: latest snapshot + recent signal events."""
    school_id = school_id_from_request(request, required=True)
    events = (
        SignalEvent.objects
        .filter(school_id=school_id, student_id=student_id)
        .order_by("-fired_at")[:50]
    )
    snap = (
        StudentRiskSnapshot.objects
        .filter(school_id=school_id, student_id=student_id)
        .order_by("-as_of_date")
        .first()
    )
    return Response({
        "snapshot": StudentRiskSnapshotSerializer(snap).data if snap else None,
        "events": SignalEventSerializer(events, many=True).data,
    })


@extend_schema(
    methods=["GET"],
    tags=["Signals"],
    summary="List intervention cases",
    description="Returns the current intervention case queue for the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    responses=InterventionCaseSerializer(many=True),
)
@extend_schema(
    methods=["POST"],
    tags=["Signals"],
    summary="Create intervention case",
    description="Creates a manual intervention case for a student in the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    request=INTERVENTION_CASE_CREATE_REQUEST,
    responses={201: InterventionCaseSerializer},
)
@api_view(["GET", "POST"])
def intervention_cases(request):
    """Staff intervention queue (GET list / POST create)."""
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        qs = (
            InterventionCase.objects
            .filter(school_id=school_id)
            .order_by("-opened_at")[:200]
        )
        return Response(InterventionCaseSerializer(qs, many=True).data)

    # POST — manual case creation
    payload = request.data or {}
    from uuid import UUID as _UUID
    student_id_raw = payload.get("student_id")
    if not student_id_raw:
        return Response({"detail": "student_id required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        student_uuid = _UUID(str(student_id_raw))
    except Exception:
        return Response({"detail": "student_id must be a valid UUID."}, status=status.HTTP_400_BAD_REQUEST)

    case = InterventionCase.objects.create(
        school_id=school_id,
        student_id=student_uuid,
        reason=payload.get("reason", "Manual intervention case"),
        priority=payload.get("priority", "MED"),
        status="OPEN",
        linked_signals=payload.get("linked_signals", []),
        owner_user_id=payload.get("owner_user_id"),
    )
    return Response(InterventionCaseSerializer(case).data, status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    tags=["Signals"],
    summary="List intervention actions",
    description="Returns the action timeline for a specific intervention case in the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    responses=InterventionActionSerializer(many=True),
)
@extend_schema(
    methods=["POST"],
    tags=["Signals"],
    summary="Create intervention action",
    description="Adds a manual action entry to an intervention case for the requesting school.",
    parameters=[SIGNALS_SCHOOL_HEADER],
    request=INTERVENTION_ACTION_CREATE_REQUEST,
    responses={201: InterventionActionSerializer},
)
@api_view(["GET", "POST"])
def intervention_actions(request, case_id):
    """Action timeline for a specific case (GET list / POST add action)."""
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        actions = (
            InterventionAction.objects
            .filter(school_id=school_id, case_id=case_id)
            .order_by("-created_at")
        )
        return Response(InterventionActionSerializer(actions, many=True).data)

    payload = request.data or {}
    created_by_user_id = int(payload.get("created_by_user_id", 0))

    action = InterventionAction.objects.create(
        school_id=school_id,
        case_id=case_id,
        action_type=payload.get("action_type", "NOTE"),
        note=payload.get("note", ""),
        created_by_user_id=created_by_user_id,
    )

    # Update case heartbeat
    InterventionCase.objects.filter(school_id=school_id, id=case_id).update(
        last_action_at=action.created_at
    )
    return Response(InterventionActionSerializer(action).data, status=status.HTTP_201_CREATED)
