from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

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


# ---------------------------------------------------------------------------
# Board read-only endpoints
# ---------------------------------------------------------------------------

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
