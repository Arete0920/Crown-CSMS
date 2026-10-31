"""Standalone AM/PM commercial entitlement and child-custody safety integration.

These tests exercise real DRF endpoints against canonical school-bound users,
without payment activation or customer records.
"""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from aftercare.models import (
    AftercareAttendance, AftercareEnrollment, AftercarePickupContact,
    AftercareProgramConfig,
)
from aftercare.services import school_local_date
from core.models import CrownPermission, RolePermission, School, Staff, UserAccount, UserRole
from households.models import Guardian, Household, Student
from subscriptions.models import SchoolModule

pytestmark = pytest.mark.django_db
API = "/api/v1/aftercare/"


def family():
    school = School.objects.create(name="Care Entitlement School", timezone="UTC")
    household = Household.objects.create(school_id=school.id, name="Synthetic Household")
    child = Student.objects.create(
        school_id=school.id, household=household, first_name="Synthetic",
        last_name="Child", grade_level="3",
    )
    staff = Staff.objects.create(
        school=school, first_name="Staff", last_name="Receiver",
        email=f"care-staff-{uuid4().hex[:8]}@example.test",
        role_type="TEACHER", status="ACTIVE",
    )
    operator = UserAccount.objects.create_user(
        username=f"care-operator-{uuid4().hex[:8]}",
        email=staff.email, password="test", school=school, staff=staff,
    )
    role = f"care_e2e_{uuid4().hex[:8]}"
    UserRole.objects.create(user=operator, school=school, role_code=role)
    for code in ("extended_care.view", "extended_care.edit", "board.view"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role, permission=permission)
    client = APIClient()
    client.force_authenticate(user=operator)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return school, household, child, operator, client


def grant(school, session, *, status="active", days=30):
    key = {"AM": "before_care", "PM": "after_care"}[session]
    return SchoolModule.objects.create(
        school=school, module_key=key, status=status,
        expiry_date=timezone.now() + timedelta(days=days),
    )


def enrollment(school, child, session):
    return AftercareEnrollment.objects.create(
        school_fk=school, student_fk=child,
        care_session=session, start_date=date(2020, 1, 1),
        days_of_week=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        billing_model="FLAT_MONTHLY",
    )


def payload(child, session):
    return {
        "student_id": str(child.id), "care_session": session,
        "start_date": "2020-01-01",
        "days_of_week": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
        "billing_model": "FLAT_MONTHLY",
    }


def test_zero_entitlements_deny_new_care_without_creating_records():
    school, _household, child, _staff, client = family()
    for session in ("AM", "PM"):
        assert client.post(API + "enrollments/", payload(child, session), format="json").status_code == 403
        assert client.get(API + f"roster/today/?care_session={session}").status_code == 403
        assert client.get(API + f"board/summary/?care_session={session}").status_code == 403
        assert client.post(API + "attendance/checkin/", {
            "student_id": str(child.id), "care_session": session,
        }, format="json").status_code == 403
    assert client.get(API + "config/").status_code == 403
    assert client.get(API + "wizard/setup/").status_code == 403
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()
    assert not AftercareAttendance.objects.filter(school_fk=school).exists()
    assert not AftercareProgramConfig.objects.filter(school_fk=school).exists()


@pytest.mark.parametrize("licensed,unlicensed", [("AM", "PM"), ("PM", "AM")])
def test_single_session_entitlement_prevents_cross_session_operations(licensed, unlicensed):
    school, _household, child, _staff, client = family()
    grant(school, licensed)
    enrollment(school, child, licensed)
    enrollment(school, child, unlicensed)  # legacy historical row
    assert client.get(API + f"roster/today/?care_session={licensed}").status_code == 200
    assert client.get(API + f"roster/today/?care_session={unlicensed}").status_code == 403
    assert client.get(API + f"board/summary/?care_session={unlicensed}").status_code == 403
    summary = client.get(API + "board/summary/")
    assert summary.status_code == 200
    assert summary.data["care_session"] == licensed
    listing = client.get(API + "enrollments/")
    assert listing.status_code == 200
    assert {row["care_session"] for row in listing.data} == {licensed}
    assert client.post(API + "enrollments/", payload(child, unlicensed), format="json").status_code == 403
    allowed = client.post(API + "attendance/checkin/", {
        "student_id": str(child.id), "care_session": licensed,
    }, format="json")
    assert allowed.status_code == 201, allowed.data
    denied = client.post(API + "attendance/checkin/", {
        "student_id": str(child.id), "care_session": unlicensed,
    }, format="json")
    assert denied.status_code == 403
    assert AftercareAttendance.objects.filter(school_fk=school).count() == 1


def test_dual_entitlements_share_a_child_without_requiring_diadem():
    school, _household, child, _staff, client = family()
    grant(school, "AM")
    grant(school, "PM")
    assert not SchoolModule.objects.filter(school=school, module_key="little_lambs").exists()
    assert client.post(API + "enrollments/", payload(child, "AM"), format="json").status_code == 201
    assert client.post(API + "enrollments/", payload(child, "PM"), format="json").status_code == 201
    assert client.get(API + "board/summary/").data["care_session"] == "ALL"
    assert {row["care_session"] for row in client.get(API + "enrollments/").data} == {"AM", "PM"}


def test_expired_pm_cannot_start_new_custody_but_must_allow_authorized_pickup():
    school, _household, child, operator, client = family()
    module = grant(school, "PM")
    enrollment(school, child, "PM")
    when = timezone.now()
    record = AftercareAttendance.objects.create(
        school_fk=school, student_fk=child,
        date=school_local_date(school.id, when), care_session="PM",
        checkin_time=when - timedelta(minutes=10),
    )
    contact = AftercarePickupContact.objects.create(
        school_fk=school, student_fk=child, name="Authorized Synthetic Guardian",
    )
    module.status = "expired"
    module.save(update_fields=["status"])
    assert client.get(API + "board/summary/?care_session=PM").status_code == 403
    assert client.post(API + "attendance/checkin/", {
        "student_id": str(child.id), "care_session": "PM",
    }, format="json").status_code == 403
    roster = client.get(API + "roster/today/?care_session=PM")
    assert roster.status_code == 200
    assert len(roster.data["rows"]) == 1
    assert roster.data["rows"][0]["student_id"] == child.pk
    assert client.get(API + f"students/{child.pk}/pickup-contacts/").status_code == 200
    with patch("aftercare.services.create_ledger_charge_aftercare", return_value="synthetic-only"):
        checked = client.post(API + "attendance/checkout/", {
            "student_id": str(child.pk), "care_session": "PM",
            "pickup_contact_id": contact.pk, "pickup_verified": True,
        }, format="json")
    assert checked.status_code == 200, checked.data
    record.refresh_from_db()
    assert record.pickup_verified and record.checkout_time is not None
    assert record.pickup_verified_by_id == operator.pk
    assert client.get(API + "roster/today/?care_session=PM").status_code == 403


def test_suspended_am_still_allows_authenticated_receiving_staff_handoff():
    school, _household, child, _staff, client = family()
    module = grant(school, "AM")
    enrollment(school, child, "AM")
    checked = client.post(API + "attendance/checkin/", {
        "student_id": str(child.pk), "care_session": "AM",
    }, format="json")
    assert checked.status_code == 201, checked.data
    module.status = "suspended"
    module.save(update_fields=["status"])
    assert client.get(API + "board/summary/?care_session=AM").status_code == 403
    assert client.get(API + "roster/today/?care_session=AM").status_code == 200
    handoff = client.post(API + "attendance/school-handoff/", {
        "student_id": str(child.id),
    }, format="json")
    assert handoff.status_code == 200, handoff.data
    assert handoff.data["handoff_verified"] is True
    assert client.get(API + "roster/today/?care_session=AM").status_code == 403


def test_unentitled_config_write_cannot_change_other_session_settings():
    school, _household, _child, _staff, client = family()
    grant(school, "AM")
    unchanged = client.get(API + "wizard/setup/")
    assert unchanged.status_code == 200
    previous_pm_time = unchanged.data["config"]["end_time"]
    denied = client.post(API + "wizard/setup/", {
        "config": {"end_time": "22:00:00"},
    }, format="json")
    assert denied.status_code == 403
    assert denied.data["code"] == "CARE_SESSION_NOT_ENABLED"
    allowed = client.post(API + "wizard/setup/", {
        "config": {"before_start_time": "06:00:00", "end_time": previous_pm_time},
    }, format="json")
    assert allowed.status_code == 200, allowed.data
    assert client.get(API + "config/").status_code == 200


def test_guardian_can_read_historical_custody_after_contract_expires_and_student_is_inactive():
    school, household, child, _staff, client = family()
    grant(school, "PM", status="expired")
    enrollment(school, child, "PM")
    AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, care_session="PM",
        date=school_local_date(school.id, timezone.now()),
        checkin_time=timezone.now() - timedelta(hours=2),
        checkout_time=timezone.now() - timedelta(hours=1), pickup_verified=True,
    )
    child.is_active = False
    child.save(update_fields=["is_active"])
    parent = UserAccount.objects.create_user(
        username=f"care-parent-{uuid4().hex[:8]}",
        email=f"care-parent-{uuid4().hex}@example.test", password="test", school=school,
    )
    Guardian.objects.create(
        school_id=school.id, household=household, account=parent,
        first_name="Synthetic", last_name="Guardian", is_primary=True,
    )
    client.force_authenticate(user=parent)
    history = client.get(API + f"parent/{child.id}/")
    assert history.status_code == 200
    assert len(history.data["attendance"]) == 1
    assert client.get(API + "roster/today/?care_session=PM").status_code == 403
    unrelated = UserAccount.objects.create_user(
        username=f"unrelated-guardian-{uuid4().hex[:8]}", password="test", school=school,
    )
    client.force_authenticate(user=unrelated)
    assert client.get(API + f"parent/{child.id}/").status_code == 403


def test_expired_diadem_subscription_never_unlocks_am_pm():
    school, _household, child, _staff, client = family()
    SchoolModule.objects.create(
        school=school, module_key="little_lambs", status="active",
        expiry_date=timezone.now() + timedelta(days=30),
    )
    for session in ("AM", "PM"):
        denied = client.post(API + "attendance/checkin/", {
            "student_id": str(child.pk), "care_session": session,
        }, format="json")
        assert denied.status_code == 403

def test_expired_pm_overnight_carryover_remains_visible_and_releasable(monkeypatch):
    """Midnight must not strand a checked-in child or misdate the late-fee cutoff."""
    school, _household, child, _staff, client = family()
    mod = grant(school, "PM")
    enrollment(school, child, "PM")
    before_midnight = datetime(2026, 10, 30, 23, 55, tzinfo=ZoneInfo("UTC"))
    after_midnight = datetime(2026, 10, 31, 0, 15, tzinfo=ZoneInfo("UTC"))
    record = AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, care_session="PM",
        date=date(2026, 10, 30), checkin_time=before_midnight,
    )
    pickup_contact = AftercarePickupContact.objects.create(
        school_fk=school, student_fk=child, name="Verified Guardian",
    )
    mod.status = "expired"
    mod.save(update_fields=["status"])
    monkeypatch.setattr("aftercare.api.timezone.now", lambda: after_midnight)
    roster = client.get(API + "roster/today/?care_session=PM")
    assert roster.status_code == 200, roster.data
    assert len(roster.data["rows"]) == 1
    assert roster.data["rows"][0]["unscheduled"] is True
    assert roster.data["rows"][0]["attendance"]["date"] == "2026-10-30"
    with patch("aftercare.services.create_ledger_charge_aftercare", return_value="synthetic-only"):
        release = client.post(API + "attendance/checkout/", {
            "student_id": str(child.pk), "pickup_contact_id": pickup_contact.pk,
            "pickup_verified": True, "care_session": "PM",
        }, format="json")
    assert release.status_code == 200, release.data
    record.refresh_from_db()
    assert record.date == date(2026, 10, 30)
    assert record.checkout_time == after_midnight
    assert record.pickup_verified is True
    assert client.get(API + "roster/today/?care_session=PM").status_code == 403


def test_active_program_cannot_check_in_child_with_unresolved_yesterday_custody(monkeypatch):
    school, _household, child, _staff, client = family()
    grant(school, "PM")
    enrollment(school, child, "PM")
    AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, care_session="PM",
        date=date(2026, 10, 30),
        checkin_time=datetime(2026, 10, 30, 23, 55, tzinfo=ZoneInfo("UTC")),
    )
    monkeypatch.setattr(
        "aftercare.api.timezone.now",
        lambda: datetime(2026, 10, 31, 0, 15, tzinfo=ZoneInfo("UTC")),
    )
    response = client.post(API + "attendance/checkin/", {
        "student_id": str(child.id), "care_session": "PM",
    }, format="json")
    assert response.status_code == 400, response.data
    assert AftercareAttendance.objects.filter(school_fk=school).count() == 1


def test_inactive_child_still_has_authorized_pm_custody_release(monkeypatch):
    school, _household, child, _staff, client = family()
    mod = grant(school, "PM")
    enrollment(school, child, "PM")
    pickup_contact = AftercarePickupContact.objects.create(
        school_fk=school, student_fk=child, name="Authorized Parent",
    )
    when = timezone.now()
    AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, date=school_local_date(school.id, when),
        care_session="PM", checkin_time=when - timedelta(minutes=5),
    )
    child.is_active = False
    child.save(update_fields=["is_active"])
    mod.status = "suspended"
    mod.save(update_fields=["status"])
    assert client.get(API + f"students/{child.pk}/pickup-contacts/").status_code == 200
    with patch("aftercare.services.create_ledger_charge_aftercare", return_value="synthetic-only"):
        release = client.post(API + "attendance/checkout/", {
            "student_id": str(child.pk), "care_session": "PM",
            "pickup_contact_id": pickup_contact.pk, "pickup_verified": True,
        }, format="json")
    assert release.status_code == 200, release.data
    assert release.data["pickup_verified"] is True



def test_stale_open_custody_remains_visible_for_supervisor_reconciliation(monkeypatch):
    """Older open attendance must not disappear from the staff custody roster."""
    school, _household, child, _staff, client = family()
    module = grant(school, "PM")
    enrollment(school, child, "PM")
    stale_day = date(2026, 10, 25)
    record = AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, care_session="PM",
        date=stale_day,
        checkin_time=datetime(2026, 10, 25, 15, 0, tzinfo=ZoneInfo("UTC")),
    )
    module.status = "expired"
    module.save(update_fields=["status"])
    current = datetime(2026, 10, 31, 15, 0, tzinfo=ZoneInfo("UTC"))
    monkeypatch.setattr("aftercare.api.timezone.now", lambda: current)
    response = client.get(API + "roster/today/?care_session=PM")
    assert response.status_code == 200, response.data
    assert len(response.data["rows"]) == 1
    assert response.data["rows"][0]["attendance"]["date"] == str(stale_day)
    assert response.data["rows"][0]["unscheduled"] is True
    record.refresh_from_db()
    assert record.checkout_time is None
    assert client.post(API + "attendance/checkin/", {
        "student_id": str(child.id), "care_session": "PM",
    }, format="json").status_code == 403
    # Old custody still requires supervisor reconciliation, not automatic release.
    contact = AftercarePickupContact.objects.create(
        school_fk=school, student_fk=child, name="Authorized Synthetic Guardian",
    )
    release = client.post(API + "attendance/checkout/", {
        "student_id": str(child.pk), "pickup_contact_id": contact.pk,
        "pickup_verified": True, "care_session": "PM",
    }, format="json")
    assert release.status_code == 400


def test_newer_custody_cannot_mask_older_unresolved_open_attendance(monkeypatch):
    """Do not release one open session while another remains unresolved."""
    school, _household, child, _operator, client = family()
    grant(school, "PM")
    enrollment(school, child, "PM")
    now = timezone.now()
    monkeypatch.setattr("aftercare.api.timezone.now", lambda: now)
    today = school_local_date(school.id, now)
    older = AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, care_session="PM",
        date=today - timedelta(days=3), checkin_time=now - timedelta(days=3),
    )
    newer = AftercareAttendance.objects.create(
        school_fk=school, student_fk=child, care_session="PM",
        date=today, checkin_time=now - timedelta(minutes=5),
    )
    contact = AftercarePickupContact.objects.create(
        school_fk=school, student_fk=child, name="Authorized Synthetic Guardian",
    )
    response = client.post(API + "attendance/checkout/", {
        "student_id": str(child.pk), "care_session": "PM",
        "pickup_contact_id": contact.pk, "pickup_verified": True,
    }, format="json")
    assert response.status_code == 400, response.data
    assert "supervisor reconciliation" in response.data["detail"]
    older.refresh_from_db()
    newer.refresh_from_db()
    assert older.checkout_time is None and newer.checkout_time is None
    assert not older.pickup_verified and not newer.pickup_verified
