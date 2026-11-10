"""Fail-closed, side-effect-free childcare authorization and check-in policy.

This module is intentionally independent of Django and of the K-12 Student model.
Callers MUST authenticate the principal, resolve a trusted tenant, supply current
DB-backed records, and enforce the decision inside a locked DB transaction.
A positive decision is not itself an attendance, enrollment or release write.

The distinct Daycare identity and enrollment persistence layer is pending;
existing aftercare APIs are deliberately NOT modified by this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str


@dataclass(frozen=True)
class Child:
    id: UUID
    school_id: UUID
    household_id: UUID
    site_id: UUID
    active: bool
    # Optional K-12 promotion reference; never required for childcare access.
    linked_student_id: UUID | None = None


@dataclass(frozen=True)
class GuardianGrant:
    school_id: UUID
    household_id: UUID
    child_id: UUID
    guardian_id: UUID
    active: bool
    verified: bool
    can_view: bool
    custody_status: str  # CLEAR / RESTRICTED / UNKNOWN
    effective_from: datetime | None = None
    effective_until: datetime | None = None


@dataclass(frozen=True)
class StaffGrant:
    school_id: UUID
    site_id: UUID
    active: bool
    may_check_in: bool


@dataclass(frozen=True)
class CareEnrollment:
    school_id: UUID
    site_id: UUID
    child_id: UUID
    program_code: str
    status: str  # ACTIVE / WAITLISTED / CANCELLED / EXPIRED
    readiness: str  # READY / BLOCKED / INCOMPLETE
    start_date: date
    end_date: date | None
    weekdays: tuple[int, ...]  # Monday=0..Sunday=6, explicitly scheduled


@dataclass(frozen=True)
class RoomPolicy:
    school_id: UUID
    site_id: UUID
    active: bool
    licensed_capacity: int | None
    max_children_per_staff: int | None  # Explicitly configured under local law


@dataclass(frozen=True)
class RoomOccupancy:
    children_present: int
    qualified_staff_present: int
    child_already_present: bool


def _ids_valid(*values: object) -> bool:
    return all(isinstance(value, UUID) and value.int != 0 for value in values)


def _bool(value: object) -> bool:
    return type(value) is bool


def guardian_read_decision(
    *,
    school_id: UUID,
    guardian_id: UUID,
    authenticated: bool,
    child: Child,
    grant: GuardianGrant,
    at: datetime,
) -> Decision:
    """Require per-child, verified guardian authority; household membership alone is insufficient."""
    if not _ids_valid(school_id, guardian_id, child.id, child.school_id,
                      child.household_id, child.site_id, grant.school_id,
                      grant.household_id, grant.child_id, grant.guardian_id):
        return Decision(False, "invalid_identity")
    if not _bool(authenticated) or not authenticated:
        return Decision(False, "authentication_required")
    if (school_id != child.school_id or grant.school_id != school_id or
        grant.child_id != child.id or grant.guardian_id != guardian_id or
        grant.household_id != child.household_id):
        return Decision(False, "scope_mismatch")
    if not all(_bool(v) and v for v in (child.active, grant.active, grant.verified, grant.can_view)):
        return Decision(False, "authority_inactive")
    if grant.custody_status != "CLEAR":
        return Decision(False, "custody_review_required")
    if not isinstance(at, datetime) or at.tzinfo is None or at.utcoffset() is None:
        return Decision(False, "invalid_time")
    for boundary in (grant.effective_from, grant.effective_until):
        if boundary is not None and (not isinstance(boundary, datetime) or
                                     boundary.tzinfo is None or boundary.utcoffset() is None):
            return Decision(False, "invalid_authority_window")
    if (grant.effective_from is not None and at < grant.effective_from or
        grant.effective_until is not None and at >= grant.effective_until):
        return Decision(False, "authority_expired")
    if (grant.effective_from is not None and grant.effective_until is not None and
        grant.effective_from >= grant.effective_until):
        return Decision(False, "invalid_authority_window")
    return Decision(True, "guardian_authorized")


def checkin_decision(
    *,
    school_id: UUID,
    site_id: UUID,
    program_code: str,
    local_date: date,
    child: Child,
    staff: StaffGrant,
    enrollment: CareEnrollment,
    room: RoomPolicy,
    occupancy: RoomOccupancy,
) -> Decision:
    """Check standing authority, specific enrollment, capacity and explicit ratio.

    NOT a lock or admission write. A transactional caller must re-read all
    current inputs under appropriate locks, re-evaluate, then persist atomically.
    The room ratio input is jurisdiction-approved configuration, not a legal default.
    """
    if not _ids_valid(school_id, site_id, child.id, child.school_id,
                      child.household_id, child.site_id, staff.school_id,
                      staff.site_id, enrollment.school_id, enrollment.site_id,
                      enrollment.child_id, room.school_id, room.site_id):
        return Decision(False, "invalid_identity")
    if not isinstance(program_code, str) or not program_code.strip():
        return Decision(False, "invalid_program")
    # datetime is a subclass of date but this interface requires an exact local day.
    if type(local_date) is not date:
        return Decision(False, "invalid_date")
    if (child.school_id != school_id or staff.school_id != school_id or
        enrollment.school_id != school_id or room.school_id != school_id or
        child.site_id != site_id or staff.site_id != site_id or
        enrollment.site_id != site_id or room.site_id != site_id or
        enrollment.child_id != child.id):
        return Decision(False, "scope_mismatch")
    if not all(_bool(v) and v for v in (child.active, staff.active,
                                         staff.may_check_in, room.active)):
        return Decision(False, "authority_inactive")
    if enrollment.status != "ACTIVE" or enrollment.readiness != "READY":
        return Decision(False, "enrollment_not_ready")
    if enrollment.program_code != program_code:
        return Decision(False, "program_mismatch")
    if (type(enrollment.start_date) is not date or
        (enrollment.end_date is not None and type(enrollment.end_date) is not date) or
        local_date < enrollment.start_date or
        (enrollment.end_date is not None and local_date > enrollment.end_date)):
        return Decision(False, "outside_enrollment_dates")
    if (not isinstance(enrollment.weekdays, tuple) or
        not enrollment.weekdays or
        any(type(day) is not int or day < 0 or day > 6 for day in enrollment.weekdays) or
        local_date.weekday() not in enrollment.weekdays):
        return Decision(False, "not_scheduled")
    if not all(type(v) is int for v in (room.licensed_capacity,
                                        room.max_children_per_staff,
                                        occupancy.children_present,
                                        occupancy.qualified_staff_present)):
        return Decision(False, "room_policy_missing")
    if (room.licensed_capacity <= 0 or room.max_children_per_staff <= 0 or
        occupancy.children_present < 0 or occupancy.qualified_staff_present <= 0):
        return Decision(False, "room_policy_invalid")
    if not _bool(occupancy.child_already_present):
        return Decision(False, "occupancy_unknown")
    if occupancy.child_already_present:
        return Decision(False, "already_checked_in")
    new_count = occupancy.children_present + 1
    if new_count > room.licensed_capacity:
        return Decision(False, "capacity_exceeded")
    if new_count > room.max_children_per_staff * occupancy.qualified_staff_present:
        return Decision(False, "ratio_exceeded")
    return Decision(True, "checkin_eligible")
