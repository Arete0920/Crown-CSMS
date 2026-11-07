"""Synthetic, inactive, director-scoped Diadem staff proposal acceptance.

Proposals cannot provide qualification, active coverage or custody authority.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.db import connection, connections
from django.utils import timezone
from rest_framework.test import APIClient

from aftercare.daycare_staff_proposals import create_staff_proposal
from aftercare.models import DaycareAttendance, DaycareRoomStaffCoverage, DaycareSite, DaycareRoom
from audit.models import AuditLog
from core.models import UserAccount, UserRole
from .test_daycare_setup import ROOM, tenant, post_site, room_url

pytestmark = pytest.mark.django_db


def _build():
    school, director, client, profile, entitlement = tenant()
    site_id = post_site(client).data["site_id"]
    room_id = client.post(room_url(site_id), ROOM, format="json").data["room_id"]
    staff_key = uuid4().hex
    staff = UserAccount.objects.create_user(
        username=f"diadem-staff-{staff_key}",
        email=f"diadem-staff-{staff_key}@example.test",
        school=school,
    )
    UserRole.objects.create(user=staff, school=school, role_code="DAYCARE_STAFF")
    starts = timezone.now() + timedelta(days=2)
    starts = starts.replace(microsecond=0)
    ends = starts + timedelta(hours=4)
    url = f"{room_url(site_id)}{room_id}/staff-proposals/"
    values = {
        "staff_id": str(staff.pk), "starts_at": starts.isoformat(),
        "ends_at": ends.isoformat(),
    }
    return school, director, client, profile, entitlement, staff, starts, ends, url, values


def test_director_proposes_inactive_staff_and_gets_persisted_scoped_readback():
    school, director, client, _, _, staff, _, _, url, values = _build()
    response = client.post(url, values, format="json")
    assert response.status_code == 201, response.data
    assert response.data["staff_id"] == str(staff.pk)
    assert response.data["is_active"] is False
    assert response.data["qualification_status"] == "NOT_VERIFIED"
    persisted = DaycareRoomStaffCoverage.objects.get(pk=response.data["proposal_id"])
    assert persisted.school_id == school.pk
    assert not persisted.is_active and not persisted.is_qualified
    assert not persisted.qualification_evidence and persisted.verified_by_id is None
    assert persisted.verified_at is None
    assert not DaycareSite.objects.get(school=school).is_active
    assert not DaycareRoom.objects.get(school=school).is_active
    read = client.get(url)
    assert read.status_code == 200 and read.data["school_id"] == str(school.pk)
    assert read.data["proposals"] == [response.data]
    event = AuditLog.objects.get(action="diadem.daycare.staff_proposal.created")
    assert event.user_id == director.pk and event.object_id == str(persisted.pk)
    assert event.metadata["qualification_verified"] is False
    assert not DaycareAttendance.objects.exists()


def test_legacy_inactive_coverage_is_not_labeled_or_replayed_as_proposal():
    school, _, client, _, _, staff, starts, ends, url, values = _build()
    room = DaycareRoom.objects.get(school=school)
    legacy = DaycareRoomStaffCoverage.objects.create(
        school=school, site=room.site, room=room, staff=staff,
        starts_at=starts, ends_at=ends,
        is_active=False, is_qualified=False, qualification_evidence="",
        verified_by=None, verified_at=None,
    )
    response = client.get(url)
    assert response.status_code == 200, response.data
    assert response.data["proposals"] == []
    replay = client.post(url, values, format="json")
    assert replay.status_code == 409, replay.data
    legacy.refresh_from_db()
    assert not legacy.is_active and not legacy.is_qualified
    assert AuditLog.objects.filter(
        action="diadem.daycare.staff_proposal.created",
    ).count() == 0


def test_identical_retry_is_idempotent_and_overlapping_shifts_conflict():
    _, _, client, _, _, _, _, _, url, values = _build()
    first = client.post(url, values, format="json")
    replay = client.post(url, values, format="json")
    assert first.status_code == 201 and replay.status_code == 200
    assert first.data == replay.data
    assert client.post(url, {**values, "ends_at": (
        timezone.now() + timedelta(days=3)).isoformat()}, format="json").status_code == 409
    assert DaycareRoomStaffCoverage.objects.count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.staff_proposal.created").count() == 1


@pytest.mark.parametrize("extra", [
    {"is_active": True}, {"is_qualified": True}, {"qualification_evidence": "self-approved"},
    {"verified_by": str(uuid4())}, {"verified_at": "2026-11-07T12:00:00Z"},
    {"school_id": str(uuid4())},
])
def test_client_cannot_self_approve_or_select_school(extra):
    _, _, client, _, _, _, _, _, url, values = _build()
    response = client.post(url, {**values, **extra}, format="json")
    assert response.status_code == 400
    assert not DaycareRoomStaffCoverage.objects.exists()
    assert not AuditLog.objects.filter(action="diadem.daycare.staff_proposal.created").exists()


def test_foreign_staff_or_room_not_disclosed():
    _, _, client, _, _, _, _, _, url, values = _build()
    other_school, _, other_client, _, _, other_staff, _, _, foreign_url, _ = _build()
    result = client.post(url, {**values, "staff_id": str(other_staff.pk)}, format="json")
    assert result.status_code == 400
    assert client.get(foreign_url).status_code == 404
    assert client.post(foreign_url, values, format="json").status_code == 404
    assert not DaycareRoomStaffCoverage.objects.exists()


@pytest.mark.parametrize("denial", ["role", "entitlement", "inactive_staff"])
def test_missing_director_entitlement_or_staff_role_denied(denial):
    school, director, client, _, entitlement, staff, _, _, url, values = _build()
    if denial == "role":
        UserRole.objects.filter(user=director, role_code="DAYCARE_DIRECTOR").delete()
    if denial == "entitlement":
        entitlement.enabled = False
        entitlement.save(update_fields=["enabled"])
    if denial == "inactive_staff":
        UserRole.objects.filter(user=staff, role_code="DAYCARE_STAFF").delete()
    result = client.post(url, values, format="json")
    assert result.status_code in (400, 401, 403, 404)
    if denial != "inactive_staff":
        assert client.get(url).status_code in (401, 403, 404)
    assert not DaycareRoomStaffCoverage.objects.exists()


@pytest.mark.parametrize("values", [
    {"starts_at": "2026-11-10T10:00:00", "ends_at": "2026-11-10T14:00:00Z"},
    {"starts_at": "2026-11-10T14:00:00Z", "ends_at": "2026-11-10T10:00:00Z"},
])
def test_invalid_offset_or_interval_denied_without_write(values):
    _, _, client, _, _, _, _, _, url, valid = _build()
    result = client.post(url, {**valid, **values}, format="json")
    assert result.status_code == 400
    assert not DaycareRoomStaffCoverage.objects.exists()


def test_audit_failure_rolls_back_proposal():
    _, _, client, _, _, _, _, _, url, values = _build()
    client.raise_request_exception = False
    with patch(
        "aftercare.daycare_staff_proposals.AuditLog.objects.create",
        side_effect=RuntimeError("synthetic audit failure"),
    ):
        assert client.post(url, values, format="json").status_code == 500
    assert not DaycareRoomStaffCoverage.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_staff_proposal_retry_is_unique_and_audited():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL row-lock proof.")
    school, director, _client, _, _, staff, starts, ends, url, _values = _build()
    barrier = Barrier(2)

    def worker():
        connections.close_all()
        try:
            barrier.wait(timeout=20)
            row, created = create_staff_proposal(
                school_id=school.pk, actor_id=director.pk,
                site_id=DaycareSite.objects.get(school=school).pk,
                room_id=DaycareRoom.objects.get(school=school).pk,
                staff_id=staff.pk, starts_at=starts, ends_at=ends,
            )
            return row.pk, created
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: worker(), range(2)))
    assert len({pk for pk, _ in outcomes}) == 1
    assert sum(created for _pk, created in outcomes) == 1
    assert DaycareRoomStaffCoverage.objects.count() == 1
    assert AuditLog.objects.filter(action="diadem.daycare.staff_proposal.created").count() == 1
