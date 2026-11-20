"""Inert #595 qualification, policy and planning approvals; synthetic only."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier
from uuid import uuid4
from unittest.mock import patch

import pytest
from django.db import connection, connections
from django.utils import timezone

from aftercare.daycare_approval import REVIEW_PERMISSION, submit_qualification
from aftercare.models import (
    DaycareAttendance, DaycareRoom, DaycareRoomStaffCoverage,
    DaycareStaffQualificationReview, DaycareRoomPolicyReview,
    DaycareStaffAssignmentReview,
)
from audit.models import AuditLog
from core.models import CrownPermission, RolePermission
from .test_daycare_staff_proposals import _build

pytestmark = pytest.mark.django_db


def _url(room, suffix):
    return (f"/api/v1/aftercare/daycare/setup/sites/{room.site_id}"
            f"/rooms/{room.pk}/{suffix}/")


def _grant():
    perm, _ = CrownPermission.objects.get_or_create(code=REVIEW_PERMISSION)
    RolePermission.objects.get_or_create(role_code="DAYCARE_DIRECTOR", permission=perm)


def _interval(start, end):
    return {
        "source_authority": "SYNTHETIC REVIEW AUTHORITY - NOT LICENSING",
        "source_reference": "SYNTHETIC-REVIEW-123",
        "effective_from": start.isoformat(),
        "effective_until": end.isoformat(),
        "request_key": str(uuid4()),
    }


def _setup():
    school, director, client, _, _, staff, starts, ends, proposal_url, proposal_values = _build()
    room = DaycareRoom.objects.get(school=school)
    proposal_response = client.post(proposal_url, proposal_values, format="json")
    assert proposal_response.status_code == 201, proposal_response.data
    return school, director, client, staff, room, starts, ends, proposal_response.data["proposal_id"]


def _qualification_payload(staff, start, end):
    return {
        **_interval(start, end),
        "staff_id": str(staff.pk),
        "qualification_code": "SYNTHETIC-TRAINING-TEST",
        "decision": "VERIFIED",
    }


def _policy_payload(start, end):
    return {
        **_interval(start, end),
        "jurisdiction": "US-DE", "policy_version": "SYNTHETIC-V1",
        "facility_license_reference": "SYNTHETIC-FACILITY-0001",
        "age_min_months": 12, "age_max_months": 23,
        "licensed_capacity": 12, "max_group_size": 12,
        "max_children_per_staff": 6, "decision": "APPROVED",
    }


def test_review_api_requires_separate_explicit_permission_by_default():
    _, _, client, staff, room, starts, ends, _ = _setup()
    url = _url(room, "qualification-reviews")
    body = _qualification_payload(staff, starts, ends)
    assert client.post(url, body, format="json").status_code == 403
    assert client.get(_url(room, "safety-reviews")).status_code == 403
    assert not DaycareStaffQualificationReview.objects.exists()


def test_qualification_review_idempotent_audited_inert_and_readback():
    _, director, client, staff, room, starts, ends, _ = _setup()
    _grant()
    url = _url(room, "qualification-reviews")
    payload = _qualification_payload(staff, starts, ends)
    first = client.post(url, payload, format="json")
    second = client.post(url, payload, format="json")
    assert first.status_code == 201, first.data
    assert second.status_code == 200, second.data
    assert first.data == second.data
    assert first.data["operational_activation"] is False
    review = DaycareStaffQualificationReview.objects.get()
    assert review.reviewed_by_id == director.pk
    assert review.staff_id == staff.pk
    assert AuditLog.objects.filter(
        action="diadem.daycare.safety_review.qualification",
        object_id=str(review.pk),
    ).count() == 1
    read = client.get(_url(room, "safety-reviews"))
    assert read.status_code == 200, read.data
    assert read.data["operational_activation"] is False
    assert read.data["qualifications"][0]["source_reference"] == payload["source_reference"]
    assert not DaycareRoomStaffCoverage.objects.get(staff=staff).is_active
    assert not room.is_active


def test_reviewer_denies_forged_fields_and_conflicting_replay():
    _, _, client, staff, room, starts, ends, _ = _setup()
    _grant()
    url = _url(room, "qualification-reviews")
    payload = _qualification_payload(staff, starts, ends)
    assert client.post(url, {**payload, "is_active": True}, format="json").status_code == 400
    assert client.post(url, {**payload, "reviewed_by_id": str(uuid4())}, format="json").status_code == 400
    assert client.post(url, payload, format="json").status_code == 201
    assert client.post(url, {**payload, "decision": "REJECTED"}, format="json").status_code == 409
    assert DaycareStaffQualificationReview.objects.count() == 1


def test_policy_review_is_not_room_approval_and_mismatched_jurisdiction_denied():
    _, _, client, _, room, starts, ends, _ = _setup()
    _grant()
    url = _url(room, "policy-reviews")
    payload = _policy_payload(starts, ends)
    assert client.post(url, {**payload, "jurisdiction": "US-XX"}, format="json").status_code == 400
    result = client.post(url, payload, format="json")
    assert result.status_code == 201, result.data
    room.refresh_from_db()
    assert not room.is_active and room.policy_verified_at is None
    assert DaycareRoomPolicyReview.objects.get().decision == "APPROVED"


def test_assignment_review_does_not_activate_coverage():
    _, _, client, staff, room, starts, ends, proposal_id = _setup()
    _grant()
    begin, until = starts - timedelta(days=1), ends + timedelta(days=1)
    qualified = client.post(_url(room, "qualification-reviews"),
                            _qualification_payload(staff, begin, until), format="json")
    policy = client.post(_url(room, "policy-reviews"),
                         _policy_payload(begin, until), format="json")
    assert qualified.status_code == 201 and policy.status_code == 201
    body = {
        **_interval(starts, ends), "proposal_id": proposal_id,
        "qualification_review_id": qualified.data["review_id"],
        "room_policy_review_id": policy.data["review_id"],
        "decision": "APPROVED",
    }
    url = _url(room, "assignment-reviews")
    response = client.post(url, body, format="json")
    assert response.status_code == 201, response.data
    assert client.post(url, body, format="json").status_code == 200
    assert DaycareStaffAssignmentReview.objects.count() == 1
    coverage = DaycareRoomStaffCoverage.objects.get(pk=proposal_id)
    assert not coverage.is_active and not coverage.is_qualified
    assert coverage.verified_at is None and not coverage.qualification_evidence
    assert not DaycareAttendance.objects.exists()


def test_revocation_keeps_prior_evidence_and_denies_stale_assignment():
    _, _, client, staff, room, starts, ends, proposal_id = _setup()
    _grant()
    begin, until = starts - timedelta(days=1), ends + timedelta(days=1)
    q = _qualification_payload(staff, begin, until)
    first = client.post(_url(room, "qualification-reviews"), q, format="json")
    assert first.status_code == 201, first.data
    revoked = {
        **_qualification_payload(staff, begin, until),
        "decision": "REVOKED",
        "supersedes_id": first.data["review_id"],
    }
    assert client.post(_url(room, "qualification-reviews"), revoked, format="json").status_code == 201
    assert DaycareStaffQualificationReview.objects.count() == 2
    policy = client.post(_url(room, "policy-reviews"),
                         _policy_payload(begin, until), format="json")
    assert policy.status_code == 201
    attempted = client.post(_url(room, "assignment-reviews"), {
        **_interval(starts, ends), "proposal_id": proposal_id,
        "qualification_review_id": first.data["review_id"],
        "room_policy_review_id": policy.data["review_id"],
        "decision": "APPROVED",
    }, format="json")
    assert attempted.status_code == 409, attempted.data
    assert not DaycareStaffAssignmentReview.objects.exists()


def test_missing_validity_and_missing_approval_never_change_coverage():
    _, _, client, staff, room, starts, ends, proposal_id = _setup()
    _grant()
    qualified = client.post(_url(room, "qualification-reviews"),
        _qualification_payload(staff, starts, ends - timedelta(minutes=1)), format="json")
    policy = client.post(_url(room, "policy-reviews"),
        _policy_payload(starts, ends), format="json")
    attempt = client.post(_url(room, "assignment-reviews"), {
        **_interval(starts, ends), "proposal_id": proposal_id,
        "qualification_review_id": qualified.data["review_id"],
        "room_policy_review_id": policy.data["review_id"],
        "decision": "APPROVED",
    }, format="json")
    assert attempt.status_code == 409
    assert not DaycareStaffAssignmentReview.objects.exists()
    assert not DaycareRoomStaffCoverage.objects.get(pk=proposal_id).is_active


def test_audit_failure_rolls_back_inert_review():
    _, _, client, staff, room, starts, ends, _ = _setup()
    _grant()
    client.raise_request_exception = False
    with patch("aftercare.daycare_approval.AuditLog.objects.create",
               side_effect=RuntimeError("synthetic audit failure")):
        response = client.post(_url(room, "qualification-reviews"),
                               _qualification_payload(staff, starts, ends), format="json")
    assert response.status_code == 500
    assert not DaycareStaffQualificationReview.objects.exists()


def test_cross_tenant_review_identity_not_accepted():
    _, _, client, _staff, room, starts, ends, _ = _setup()
    foreign_school, _, _, foreign_staff, _, _, _, _ = _setup()
    _grant()
    payload = _qualification_payload(foreign_staff, starts, ends)
    result = client.post(_url(room, "qualification-reviews"), payload, format="json")
    assert result.status_code == 400
    assert not DaycareStaffQualificationReview.objects.exists()

@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_safety_review_retry_is_unique_and_audited():
    if connection.vendor != "postgresql":
        pytest.skip("Requires PostgreSQL; enforced as non-skippable in dedicated safety CI.")
    school, director, _client, staff, room, starts, ends, _ = _setup()
    _grant()
    barrier = Barrier(2)
    key = uuid4()
    values = {
        "staff_id": staff.pk, "qualification_code": "SYNTHETIC-RACE",
        "decision": "VERIFIED", "source_authority": "SYNTHETIC NOT LICENSING",
        "source_reference": "RACE-REVIEW-0001",
        "effective_from": starts, "effective_until": ends, "request_key": key,
    }

    def worker():
        connections.close_all()
        try:
            barrier.wait(timeout=20)
            review, created = submit_qualification(
                school_id=school.pk, actor_id=director.pk,
                site_id=room.site_id, room_id=room.pk, values=values,
            )
            return review.pk, created
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(lambda _: worker(), range(2)))
    assert len({pk for pk, _ in outcomes}) == 1
    assert sum(created for _, created in outcomes) == 1
    assert DaycareStaffQualificationReview.objects.count() == 1
    assert AuditLog.objects.filter(
        action="diadem.daycare.safety_review.qualification",
    ).count() == 1
    assert not DaycareRoomStaffCoverage.objects.get(staff=staff).is_active

def test_new_decision_must_explicitly_supersede_the_current_subject():
    _, _, client, staff, room, starts, ends, _ = _setup()
    _grant()
    url = _url(room, "qualification-reviews")
    first = _qualification_payload(staff, starts, ends)
    assert client.post(url, first, format="json").status_code == 201
    competing = _qualification_payload(staff, starts, ends)
    assert client.post(url, competing, format="json").status_code == 409
    replacement = {**competing, "decision": "REJECTED",
                   "supersedes_id": str(DaycareStaffQualificationReview.objects.get().pk)}
    response = client.post(url, replacement, format="json")
    assert response.status_code == 201, response.data
    assert client.post(url, replacement, format="json").status_code == 200
    assert DaycareStaffQualificationReview.objects.count() == 2
    assert client.get(_url(room, "safety-reviews")).data["qualifications"][0]["superseded"] is True


def test_unaudited_direct_orm_review_is_not_trusted_or_disclosed():
    school, director, client, staff, room, starts, ends, proposal_id = _setup()
    _grant()
    # Privileged direct model writes do not carry transactional review provenance.
    ghost = DaycareStaffQualificationReview.objects.create(
        school=school, site=room.site, staff=staff,
        reviewed_by=director, reviewed_at=timezone.now(),
        effective_from=starts, effective_until=ends,
        source_authority="SYNTHETIC UNATTRIBUTED",
        source_reference="NO-AUDIT-RECORD",
        qualification_code="SYNTHETIC-TRAINING-TEST",
        decision="VERIFIED", request_key=uuid4(),
    )
    read = client.get(_url(room, "safety-reviews"))
    assert read.status_code == 200
    assert read.data["qualifications"] == []
    # A real audited policy cannot turn an unaudited qualification into a
    # valid assignment planning review.
    policy = client.post(
        _url(room, "policy-reviews"), _policy_payload(starts, ends),
        format="json",
    )
    assert policy.status_code == 201, policy.data
    attempt = client.post(_url(room, "assignment-reviews"), {
        **_interval(starts, ends), "proposal_id": proposal_id,
        "qualification_review_id": str(ghost.pk),
        "room_policy_review_id": policy.data["review_id"],
        "decision": "APPROVED",
    }, format="json")
    assert attempt.status_code == 409, attempt.data
    assert not DaycareStaffAssignmentReview.objects.exists()


def test_director_cannot_read_qualification_reviews_for_another_room():
    school, director, client, staff, room, starts, ends, _ = _setup()
    _grant()
    qualified = client.post(
        _url(room, "qualification-reviews"),
        _qualification_payload(staff, starts, ends), format="json",
    )
    assert qualified.status_code == 201, qualified.data
    from .test_daycare_setup import ROOM, room_url
    other_room = client.post(
        room_url(room.site_id), {**ROOM, "code": "room-b"},
        format="json",
    )
    assert other_room.status_code == 201, other_room.data
    other_read = client.get(
        _url(DaycareRoom.objects.get(pk=other_room.data["room_id"]), "safety-reviews")
    )
    assert other_read.status_code == 200, other_read.data
    assert other_read.data["qualifications"] == []
