"""Director-only staff scheduling proposals; never qualify, activate or approve staff.

Every proposed assignment is tenant-bound, inactive and unverified. Live custody
service authority continues to depend on separate reviewed coverage activation.
"""
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import NotFound, ValidationError

from audit.models import AuditLog
from core.models import UserAccount, UserRole
from .daycare_checkin_models import DaycareRoomStaffCoverage
from .daycare_models import DaycareRoom, DaycareSite
from .daycare_setup import require_configuration


class StaffProposalConflict(Exception):
    pass


def _site_and_room(school, site_id, room_id, *, lock=False):
    sites = DaycareSite.objects
    rooms = DaycareRoom.objects
    # Lock site then room so director writes follow a stable lock order.
    if lock:
        sites = sites.select_for_update()
        rooms = rooms.select_for_update()
    site = sites.filter(pk=site_id, school=school).first()
    if site is None:
        raise NotFound()
    room = rooms.filter(pk=room_id, school=school, site=site).first()
    if room is None:
        raise NotFound()
    return site, room


def staff_proposal_data(coverage):
    return {
        "proposal_id": str(coverage.pk),
        "staff_id": str(coverage.staff_id),
        "starts_at": coverage.starts_at.isoformat(),
        "ends_at": coverage.ends_at.isoformat(),
        "is_active": False,
        "qualification_status": "NOT_VERIFIED",
        "approval_status": "NOT_APPROVED",
    }


def list_staff_proposals(*, school_id, actor_id, site_id, room_id):
    with transaction.atomic():
        school, _actor = require_configuration(school_id, actor_id)
        site, room = _site_and_room(school, site_id, room_id)
        rows = DaycareRoomStaffCoverage.objects.filter(
            school=school, site=site, room=room,
            is_active=False, is_qualified=False, verified_by__isnull=True,
        ).order_by("starts_at", "pk")
        return {
            "school_id": str(school.pk),
            "site_id": str(site.pk),
            "room_id": str(room.pk),
            "as_of": timezone.now().isoformat(),
            "source": "aftercare.DaycareRoomStaffCoverage",
            "proposals": [staff_proposal_data(item) for item in rows],
        }


def create_staff_proposal(*, school_id, actor_id, site_id, room_id,
                          staff_id, starts_at, ends_at):
    """One inactive proposal per staff/time, across all tenant-local rooms.

    The source staff account is locked after the site/room, preventing concurrent
    proposals on two different rooms from creating conflicting scheduled shifts.
    Existing active or independently reviewed coverage is never overwritten.
    """
    if not starts_at < ends_at:
        raise ValidationError({"detail": "Proposed staff interval must be ordered."})
    with transaction.atomic():
        school, actor = require_configuration(school_id, actor_id)
        site, room = _site_and_room(school, site_id, room_id, lock=True)
        staff = UserAccount.objects.select_for_update().filter(
            pk=staff_id, school=school, is_active=True,
        ).first()
        if staff is None or not UserRole.objects.filter(
            user=staff, school=school, role_code="DAYCARE_STAFF",
        ).exists():
            # Do not distinguish foreign/nonexistent staff identities.
            raise ValidationError({"detail": "Proposed staff identity is invalid."})
        # Includes already-active shifts and inactive proposals from another room.
        overlaps = DaycareRoomStaffCoverage.objects.filter(
            school=school, staff=staff,
            starts_at__lt=ends_at, ends_at__gt=starts_at,
        )
        exact = overlaps.filter(
            site=site, room=room, starts_at=starts_at, ends_at=ends_at,
        ).first()
        if exact is not None:
            if (exact.is_active or exact.is_qualified or
                    exact.verified_by_id is not None or exact.verified_at is not None):
                raise StaffProposalConflict("Existing reviewed assignment is not a proposal.")
            if overlaps.exclude(pk=exact.pk).exists():
                raise StaffProposalConflict("Staff already has overlapping coverage.")
            return exact, False
        if overlaps.exists():
            raise StaffProposalConflict("Staff already has overlapping coverage.")
        proposal = DaycareRoomStaffCoverage.objects.create(
            school=school, site=site, room=room, staff=staff,
            starts_at=starts_at, ends_at=ends_at,
            is_active=False, is_qualified=False, qualification_evidence="",
            verified_by=None, verified_at=None,
        )
        AuditLog.objects.create(
            user_id=actor.pk, action="diadem.daycare.staff_proposal.created",
            model="DaycareRoomStaffCoverage", object_id=str(proposal.pk),
            metadata={
                "school_id": str(school.pk), "site_id": str(site.pk),
                "room_id": str(room.pk), "staff_id": str(staff.pk),
                "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat(),
                "is_active": False, "qualification_verified": False,
            },
        )
        return proposal, True
