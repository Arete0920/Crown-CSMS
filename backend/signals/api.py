from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from academics.experience_access import is_leader, role_codes, taught_sections
from academics.models import Enrollment
from academics.family_views import text, timestamp
from academics.submission_workflow_views import _uuid
from django.contrib.auth import get_user_model
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


def _board_access(request, school):
    if not request.user.is_active or not (is_leader(request.user, school) or role_codes(request.user, school) & {'BOARD', 'BOARD_MEMBER', 'board', 'school_board'}):
        raise PermissionDenied('Explicit school leadership or board authority required.')


def _staff_cases(request, school):
    qs = InterventionCase.objects.filter(school_id=school, student__school_id=school)
    if is_leader(request.user, school): return qs
    staff = getattr(request.user, 'staff', None)
    if not staff or staff.school_id != school or staff.status != 'ACTIVE' or not role_codes(request.user, school) & {'TEACHER', 'teacher'}:
        raise PermissionDenied('Active instructional staff authority required.')
    students = Enrollment.objects.filter(school_id=school, section__in=taught_sections(request.user, school)).values('student_id')
    return qs.filter(owner_account=request.user, student_id__in=students)


# ---------------------------------------------------------------------------
# Board read-only endpoints
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def board_compass_summary(request):
    """Crown Compass 2.0 — latest computed indexes + highlights/watchlist."""
    school_id = school_id_from_request(request, required=True)
    _board_access(request, school_id)
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
@permission_classes([IsAuthenticated])
def board_risk_counts(request):
    """Count of LOW/MED/HIGH risk students based on the most recent snapshot."""
    school_id = school_id_from_request(request, required=True)
    _board_access(request, school_id)
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
@permission_classes([IsAuthenticated])
def student_signals(request, student_id):
    """Per-student: latest snapshot + recent signal events."""
    school_id = school_id_from_request(request, required=True)
    if not is_leader(request.user, school_id):
        raise PermissionDenied('Raw signal drivers require school leadership.')
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
@permission_classes([IsAuthenticated])
def intervention_cases(request):
    """Staff intervention queue (GET list / POST create)."""
    school_id = school_id_from_request(request, required=True)

    scoped = _staff_cases(request, school_id)
    if request.method == 'GET':
        return Response(InterventionCaseSerializer(scoped.order_by('-opened_at')[:200], many=True).data)
    payload = request.data
    if not isinstance(payload, dict): raise ValidationError('Request must be an object.')
    from households.models import Student
    from academics.assignment_teacher_views import _can_manage_section
    student = get_object_or_404(Student, id=_uuid(payload.get('student_id'), 'student_id'), school_id=school_id)
    sections = taught_sections(request.user, school_id).filter(enrollments__student=student)
    if not is_leader(request.user, school_id) and not any(_can_manage_section(request.user, school_id, row) for row in sections):
        raise PermissionDenied('Assigned student relationship required.')
    if payload.get('owner_user_id') is not None:
        raise ValidationError('Use owner_account_id; legacy integer owner identities cannot be inferred.')
    owner = get_object_or_404(get_user_model(), id=_uuid(payload.get('owner_account_id', str(request.user.id)), 'owner_account_id'), is_active=True)
    if owner != request.user and not is_leader(request.user, school_id): raise PermissionDenied('Leadership assigns other case owners.')
    if owner != request.user and not is_leader(owner, school_id) and not taught_sections(owner, school_id).filter(enrollments__student=student).exists():
        raise ValidationError('Owner must have an authorized school relationship.')
    priority = payload.get('priority', 'MED')
    if priority not in {'LOW', 'MED', 'HIGH'}: raise ValidationError('Invalid priority.')
    review = timestamp(payload, 'review_at')
    if review <= timezone.now(): raise ValidationError('Choose a future review date.')
    with transaction.atomic():
        case = InterventionCase.objects.create(school_id=school_id, student=student, owner_account=owner,
                   reason=text(payload, 'reason', 200), priority=priority, review_at=review)
        InterventionAction.objects.create(school_id=school_id, case=case, created_by_account=request.user,
                                         action_type='PLAN', note=case.reason)
    return Response(InterventionCaseSerializer(case).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def intervention_actions(request, case_id):
    """Action timeline for a specific case (GET list / POST add action)."""
    school_id = school_id_from_request(request, required=True)

    case = get_object_or_404(_staff_cases(request, school_id), id=case_id)
    if request.method == 'GET':
        return Response(InterventionActionSerializer(case.actions.filter(school_id=school_id).order_by('-created_at'), many=True).data)
    payload = request.data
    if not isinstance(payload, dict): raise ValidationError('Request must be an object.')
    kind = payload.get('action_type', 'NOTE')
    if kind not in {'NOTE', 'CALL', 'MEETING', 'PLAN', 'FOLLOWUP'}: raise ValidationError('Invalid case action type.')
    with transaction.atomic():
        case = InterventionCase.objects.select_for_update().get(id=case.id)
        if case.status == 'CLOSED': raise ValidationError('Reopen the case through the versioned classroom workflow before adding actions.')
        action = InterventionAction.objects.create(school_id=school_id, case=case, action_type=kind,
                  note=text(payload, 'note'), created_by_account=request.user)
        case.last_action_at=action.created_at; case.version += 1; case.save()
    return Response(InterventionActionSerializer(action).data, status=status.HTTP_201_CREATED)
