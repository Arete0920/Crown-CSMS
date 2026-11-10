"""Commercial care entitlements with separate custody-continuity access.

Entitlement checks are tenant-scoped, fail closed and never replace school RBAC.
An expired sale must not strand a child already checked in: existing open custody
remains visible to authorized staff until verified handoff / authorized pickup.
"""
from subscriptions.gates import school_has_module

from .models import AftercareAttendance

CARE_KEYS = {"AM": "before_care", "PM": "after_care"}


def entitled_sessions(school_id):
    return tuple(session for session, key in CARE_KEYS.items() if school_has_module(school_id, key))


def has_open_custody(school_id, session, student_id=None):
    if session not in CARE_KEYS:
        return False
    qs = AftercareAttendance.objects.filter(
        school_fk_id=school_id, care_session=session,
        checkin_time__isnull=False, checkout_time__isnull=True,
    )
    if student_id is not None:
        qs = qs.filter(student_fk_id=student_id)
    return qs.exists()


def visible_sessions(school_id):
    """Only entitled sessions plus sessions with unfinished child custody."""
    return tuple(session for session in CARE_KEYS if
                 school_has_module(school_id, CARE_KEYS[session]) or
                 has_open_custody(school_id, session))


def disallowed_config_session(serializer, config, school_id):
    """Return an unentitled AM/PM session only for an actual field change.

    Wizards may post previously loaded unchanged fields for both sessions.
    DRF validated_data handles times/decimals and prevents string mismatches.
    """
    fields = {
        "AM": ("before_start_time", "before_end_time"),
        "PM": ("start_time", "end_time", "late_fee_per_10_min",
               "late_fee_grace_minutes", "late_fee_cap"),
    }
    for session, keys in fields.items():
        if school_has_module(school_id, CARE_KEYS[session]):
            continue
        if any(key in serializer.validated_data and
               serializer.validated_data[key] != getattr(config, key)
               for key in keys):
            return session
    return None
