"""Pure fail-closed custody release policy.

These trusted snapshots must originate from current, tenant-scoped database rows.
The policy does not verify a person's physical ID: identity_verified is a
staff-attributed, in-person attestation, not a biometric or ID scan.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from .daycare_policy import Child, Decision


@dataclass(frozen=True)
class CheckedIn:
    school_id: UUID
    site_id: UUID
    room_id: UUID
    child_id: UUID
    care_date: date
    checked_in_at: datetime
    released: bool


@dataclass(frozen=True)
class ReleasingStaff:
    school_id: UUID
    site_id: UUID
    room_id: UUID
    actor_id: UUID
    active: bool
    qualified_on_duty: bool
    may_release: bool


@dataclass(frozen=True)
class RecipientAuthority:
    school_id: UUID
    household_id: UUID
    child_id: UUID
    guardian_id: UUID
    active: bool
    verified: bool
    can_pickup: bool
    custody_status: str
    effective_from: datetime | None
    effective_until: datetime | None


IDENTITY_METHODS = frozenset({"GOVERNMENT_PHOTO_ID", "APPROVED_PHOTO_ROSTER", "PERSONALLY_KNOWN"})


def _aware(value: object) -> bool:
    return isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None


def release_decision(
    *, school_id: UUID, site_id: UUID, actor_id: UUID, guardian_id: UUID,
    child: Child, attendance: CheckedIn, staff: ReleasingStaff,
    authority: RecipientAuthority, at: datetime, local_day: date,
    authenticated: bool, identity_verified: bool, identity_method: str,
) -> Decision:
    """All checks required; no release mutation happens here."""
    identities = (
        school_id, site_id, actor_id, guardian_id,
        child.id, child.school_id, child.household_id, child.site_id,
        attendance.school_id, attendance.site_id, attendance.room_id, attendance.child_id,
        staff.school_id, staff.site_id, staff.room_id, staff.actor_id,
        authority.school_id, authority.household_id, authority.child_id, authority.guardian_id,
    )
    if any(not isinstance(value, UUID) or value.int == 0 for value in identities):
        return Decision(False, "invalid_identity")
    if type(authenticated) is not bool or not authenticated:
        return Decision(False, "authentication_required")
    if (
        school_id != child.school_id or school_id != attendance.school_id
        or school_id != staff.school_id or school_id != authority.school_id
        or site_id != child.site_id or site_id != attendance.site_id
        or site_id != staff.site_id or child.id != attendance.child_id
        or child.id != authority.child_id or child.household_id != authority.household_id
        or actor_id != staff.actor_id or guardian_id != authority.guardian_id
        or staff.room_id != attendance.room_id
    ):
        return Decision(False, "scope_mismatch")
    if not all(type(flag) is bool and flag for flag in (
        child.active, staff.active, staff.qualified_on_duty, staff.may_release,
    )):
        return Decision(False, "staff_or_child_inactive")
    if type(attendance.released) is not bool:
        return Decision(False, "attendance_state_unknown")
    if attendance.released:
        return Decision(False, "already_released")
    if not _aware(at) or not _aware(attendance.checked_in_at) or type(local_day) is not date or type(attendance.care_date) is not date:
        return Decision(False, "invalid_time")
    if at < attendance.checked_in_at:
        return Decision(False, "release_before_checkin")
    if local_day != attendance.care_date:
        return Decision(False, "overnight_release_requires_director_review")
    if not all(type(flag) is bool and flag for flag in (
        authority.active, authority.verified, authority.can_pickup,
    )):
        return Decision(False, "recipient_not_authorized")
    if authority.custody_status != "CLEAR":
        return Decision(False, "custody_review_required")
    if authority.effective_from is not None and not _aware(authority.effective_from):
        return Decision(False, "invalid_authority_window")
    if authority.effective_until is not None and not _aware(authority.effective_until):
        return Decision(False, "invalid_authority_window")
    if authority.effective_from is not None and authority.effective_until is not None and authority.effective_from >= authority.effective_until:
        return Decision(False, "invalid_authority_window")
    if authority.effective_from is not None and at < authority.effective_from:
        return Decision(False, "authority_outside_window")
    if authority.effective_until is not None and at >= authority.effective_until:
        return Decision(False, "authority_outside_window")
    if type(identity_verified) is not bool or not identity_verified or identity_method not in IDENTITY_METHODS:
        return Decision(False, "identity_verification_required")
    return Decision(True, "authorized_release")
