from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.permissions import CrownModulePermission

from .models import AccountabilityEvent, AccountabilityState
from .serializers import (
    AccountabilityEventSerializer,
    AccountabilityStateSerializer,
    AccountabilityTransitionSerializer,
)
from .services import (
    AccountabilityConflict,
    InvalidAccountabilityTransition,
    transition_student,
)


def _require_school(request):
    school = getattr(request, "school", None)
    if school is None:
        raise PermissionDenied("Tenant context required.")
    return school


@api_view(["GET"])
@permission_classes([CrownModulePermission("accountability.view")])
def current_state(request, student_id):
    school = _require_school(request)
    state = AccountabilityState.objects.filter(
        school_id=school.id, student_id=student_id
    ).first()
    if state is None:
        return Response({"detail": "No accountability state found."}, status=status.HTTP_404_NOT_FOUND)
    return Response(AccountabilityStateSerializer(state).data)


@api_view(["GET"])
@permission_classes([CrownModulePermission("accountability.view")])
def event_history(request, student_id):
    school = _require_school(request)
    events = AccountabilityEvent.objects.filter(
        school_id=school.id, student_id=student_id
    ).order_by("-occurred_at", "-id")[:200]
    return Response(AccountabilityEventSerializer(events, many=True).data)


@api_view(["POST"])
@permission_classes([CrownModulePermission("accountability.transition")])
def transition(request):
    school = _require_school(request)
    serializer = AccountabilityTransitionSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    payload = serializer.validated_data

    try:
        result = transition_student(
            school=school,
            student_id=payload["student_id"],
            actor_user=request.user,
            event_type=payload["event_type"],
            normal_state=payload.get("normal_state"),
            emergency_state=payload.get("emergency_state"),
            location_code=payload.get("location_code"),
            expected_destination=payload.get("expected_destination"),
            source_domain=payload.get("source_domain", "accountability"),
            source_record_id=payload.get("source_record_id"),
            context=payload.get("context"),
            expected_version=payload.get("expected_version"),
        )
    except AccountabilityConflict as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_409_CONFLICT)
    except InvalidAccountabilityTransition as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(
        {
            "state": AccountabilityStateSerializer(result.state).data,
            "event": AccountabilityEventSerializer(result.event).data,
        },
        status=status.HTTP_200_OK,
    )
