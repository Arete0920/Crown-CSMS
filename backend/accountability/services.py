from dataclasses import dataclass

from django.db import transaction

from core.audit import audit_event
from households.models import Student

from .models import (
    AccountabilityEvent,
    AccountabilityState,
    EMERGENCY_STATE_CHOICES,
    NORMAL_STATE_CHOICES,
)


NORMAL_STATES = {value for value, _ in NORMAL_STATE_CHOICES}
EMERGENCY_STATES = {value for value, _ in EMERGENCY_STATE_CHOICES}


class AccountabilityConflict(RuntimeError):
    pass


class InvalidAccountabilityTransition(ValueError):
    pass


@dataclass(frozen=True)
class TransitionResult:
    state: AccountabilityState
    event: AccountabilityEvent


def _validate_state(value, allowed, label):
    if value is not None and value not in allowed:
        raise InvalidAccountabilityTransition(f"Invalid {label}: {value}")


@transaction.atomic
def transition_student(
    *,
    school,
    student_id,
    actor_user,
    event_type,
    normal_state=None,
    emergency_state=None,
    location_code=None,
    responsible_user=None,
    expected_destination=None,
    source_domain="accountability",
    source_record_id=None,
    context=None,
    expected_version=None,
):
    """
    Apply one serialized accountability transition and append immutable evidence.

    At least one projected field must be supplied. expected_version provides
    optimistic conflict detection for offline/device reconciliation.
    """
    _validate_state(normal_state, NORMAL_STATES, "normal state")
    _validate_state(emergency_state, EMERGENCY_STATES, "emergency state")

    if not event_type or not str(event_type).strip():
        raise InvalidAccountabilityTransition("event_type is required.")

    student = Student.objects.filter(pk=student_id, school_id=school.id).first()
    if student is None:
        raise InvalidAccountabilityTransition("Student does not belong to this school.")

    state = (
        AccountabilityState.objects.select_for_update()
        .filter(school_id=school.id, student_id=student.id)
        .first()
    )

    if state is None:
        state = AccountabilityState.objects.create(
            school_id=school.id,
            student=student,
            normal_state="EXPECTED_ON_CAMPUS",
            version=1,
        )

    if expected_version is not None and state.version != expected_version:
        raise AccountabilityConflict(
            f"State version conflict: expected {expected_version}, current {state.version}."
        )

    before_normal = state.normal_state
    before_emergency = state.emergency_state or ""

    changed = False
    if normal_state is not None and normal_state != state.normal_state:
        state.normal_state = normal_state
        changed = True
    if emergency_state is not None and emergency_state != state.emergency_state:
        state.emergency_state = emergency_state
        changed = True
    if location_code is not None and location_code != state.location_code:
        state.location_code = location_code
        changed = True
    if responsible_user is not None and responsible_user != state.responsible_user:
        state.responsible_user = responsible_user
        changed = True
    if expected_destination is not None and expected_destination != state.expected_destination:
        state.expected_destination = expected_destination
        changed = True
    if source_domain != state.source_domain:
        state.source_domain = source_domain
        changed = True
    if source_record_id != state.source_record_id:
        state.source_record_id = source_record_id
        changed = True

    if not changed:
        raise InvalidAccountabilityTransition("Transition produced no state change.")

    state.version += 1
    state.save()

    event = AccountabilityEvent.objects.create(
        school_id=school.id,
        student=student,
        event_type=str(event_type).strip(),
        from_normal_state=before_normal,
        to_normal_state=state.normal_state,
        from_emergency_state=before_emergency,
        to_emergency_state=state.emergency_state or "",
        location_code=state.location_code,
        actor_user=actor_user,
        source_domain=source_domain,
        source_record_id=source_record_id,
        context=context or {},
        state_version=state.version,
    )

    audit_event(
        "accountability.transition",
        user=actor_user,
        school=school,
        extra={
            "student_id": str(student.id),
            "event_id": str(event.id),
            "event_type": event.event_type,
            "state_version": state.version,
        },
    )

    return TransitionResult(state=state, event=event)
