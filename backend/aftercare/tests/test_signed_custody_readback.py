"""Signed-token, temporary-DB proof of two-school AM/PM custody transitions.

This deliberately operates only on pytest's isolated fictional records.
It is not a live child-care procedure or a real-browser/physical custody audit.
"""
from datetime import datetime, timedelta, timezone as dt_timezone

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from aftercare.models import AftercareAttendance, AftercareEnrollment, AftercarePickupContact
from core.models import CrownPermission, RolePermission, School, Staff, UserAccount, UserRole
from crown_api.jwt_utils import build_access_token
from households.models import Household, Student
from subscriptions.models import SchoolModule


pytestmark = pytest.mark.django_db
ROSTER = "/api/v1/aftercare/roster/today/"
CHECKIN = "/api/v1/aftercare/attendance/checkin/"
HANDOFF = "/api/v1/aftercare/attendance/school-handoff/"
CHECKOUT = "/api/v1/aftercare/attendance/checkout/"


def _fictional_school(label):
    school = School.objects.create(name=f"Fictional Care School {label}", timezone="America/New_York")
    for key in ("before_care", "after_care"):
        SchoolModule.objects.create(
            school=school, module_key=key, status="active",
            expiry_date=timezone.now() + timedelta(days=30),
        )
    household = Household.objects.create(school_id=school.pk, name=f"Fictional Household {label}")
    child = Student.objects.create(
        school_id=school.pk, household=household,
        first_name="Fictional", last_name=f"Child {label}", grade_level="4",
    )
    for session in ("AM", "PM"):
        AftercareEnrollment.objects.create(
            school_fk=school, student_fk=child, care_session=session,
            start_date=datetime(2025, 1, 1).date(), days_of_week=["WED"],
            billing_model="FLAT_MONTHLY",
        )
    staff = Staff.objects.create(
        school=school, first_name=f"Fictional {label}", last_name="Staff",
        email=f"fictional-care-{label.lower()}@example.test",
        role_type="TEACHER", status="ACTIVE",
    )
    user = UserAccount.objects.create_user(
        username=f"fictional-care-{label.lower()}-staff",
        email=f"fictional-care-login-{label.lower()}@example.test",
        password="unused-test-only", school=school, staff=staff,
    )
    # An ordinary care operator must NOT have SUPPORT's cross-school override.
    UserRole.objects.create(user=user, school=school, role_code="AFTERCARE_STAFF")
    for code in ("extended_care.view", "extended_care.edit"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="AFTERCARE_STAFF", permission=permission)
    return school, child, user


def _signed_client(user, school, token_kind):
    if token_kind == "heritage":
        token = build_access_token(user_id=str(user.pk), email=user.email,
                                   role="aftercare_staff", school_id=str(user.school_id))
    else:
        token = AccessToken.for_user(user)
        token["school_id"] = str(user.school_id)
    client = APIClient()
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_SCHOOL_ID=str(school.pk),
    )
    return client


def _row(response, child):
    assert response.status_code == 200, getattr(response, "data", None)
    matches = [
        item for item in response.data["rows"]
        if str(item["student_id"]) == str(child.pk)
    ]
    assert len(matches) == 1, response.data
    return matches[0]


@pytest.mark.parametrize("token_kind", ["simplejwt", "heritage"])
def test_signed_two_school_custody_readback_isolation_and_verified_release(monkeypatch, token_kind):
    """A's signed staff proves custody through real Django writes and reads.

    B's signed staff cannot view or mutate A's child. A's two care sessions
    remain distinct, and a second release does not replay either operation.
    """
    school_a, child_a, staff_a = _fictional_school("A")
    school_b, child_b, staff_b = _fictional_school("B")
    client_a = _signed_client(staff_a, school_a, token_kind)
    client_b = _signed_client(staff_b, school_b, token_kind)

    # Fix a synthetic school-local Wednesday with real Eastern AM/PM hours.
    clock = [datetime(2025, 9, 3, 12, 0, tzinfo=dt_timezone.utc)]
    monkeypatch.setattr("aftercare.api.timezone.now", lambda: clock[0])
    monkeypatch.setattr("aftercare.services.timezone.now", lambda: clock[0])

    am_a = client_a.get(ROSTER, {"care_session": "AM"})
    am_b = client_b.get(ROSTER, {"care_session": "AM"})
    assert _row(am_a, child_a)["attendance"] is None
    assert _row(am_b, child_b)["attendance"] is None
    assert "Child B" not in str(am_a.data)
    assert "Child A" not in str(am_b.data)

    # A's bearer cannot select B or write to B, regardless of header spoofing.
    wrong = _signed_client(staff_a, school_b, token_kind)
    denied = wrong.get(ROSTER, {"care_session": "AM"})
    assert denied.status_code in (400, 403, 404)
    assert "Child B" not in str(getattr(denied, "data", denied.content))
    denied_write = wrong.post(CHECKIN, {
        "student_id": str(child_b.pk), "care_session": "AM",
    }, format="json")
    assert denied_write.status_code in (400, 403, 404)
    assert not AftercareAttendance.objects.filter(school_fk=school_b).exists()

    admitted = client_a.post(CHECKIN, {
        "student_id": str(child_a.pk), "care_session": "AM",
    }, format="json")
    assert admitted.status_code == 201, getattr(admitted, "data", None)
    checked_am = _row(client_a.get(ROSTER, {"care_session": "AM"}), child_a)["attendance"]
    assert checked_am["checkin_time"] and not checked_am["checkout_time"]
    assert _row(client_b.get(ROSTER, {"care_session": "AM"}), child_b)["attendance"] is None

    clock[0] = datetime(2025, 9, 3, 14, 0, tzinfo=dt_timezone.utc)
    acknowledged = client_a.post(HANDOFF, {
        "student_id": str(child_a.pk),
    }, format="json")
    assert acknowledged.status_code == 200, getattr(acknowledged, "data", None)
    handoff = _row(client_a.get(ROSTER, {"care_session": "AM"}), child_a)["attendance"]
    assert handoff["handoff_verified"] is True
    assert handoff["handoff_time"] and handoff["checkout_time"]

    clock[0] = datetime(2025, 9, 3, 20, 0, tzinfo=dt_timezone.utc)
    admitted_pm = client_a.post(CHECKIN, {
        "student_id": str(child_a.pk), "care_session": "PM",
    }, format="json")
    assert admitted_pm.status_code == 201, getattr(admitted_pm, "data", None)
    pm_before = _row(client_a.get(ROSTER, {"care_session": "PM"}), child_a)["attendance"]
    assert pm_before["checkin_time"] and not pm_before["checkout_time"]
    assert _row(client_b.get(ROSTER, {"care_session": "PM"}), child_b)["attendance"] is None

    contact = AftercarePickupContact.objects.create(
        school_fk=school_a, student_fk=child_a, name="Fictional Authorized Guardian",
        is_active=True,
    )
    clock[0] = datetime(2025, 9, 3, 21, 0, tzinfo=dt_timezone.utc)
    released = client_a.post(CHECKOUT, {
        "student_id": str(child_a.pk), "care_session": "PM",
        "pickup_contact_id": contact.pk, "pickup_verified": True,
    }, format="json")
    assert released.status_code == 200, getattr(released, "data", None)
    pm_after = _row(client_a.get(ROSTER, {"care_session": "PM"}), child_a)["attendance"]
    assert pm_after["pickup_verified"] is True and pm_after["checkout_time"]
    persisted = AftercareAttendance.objects.get(
        school_fk=school_a, student_fk=child_a, care_session="PM",
    )
    assert persisted.pickup_verified_by_id == staff_a.pk
    assert persisted.pickup_contact_fk_id == contact.pk
    stored_am = AftercareAttendance.objects.get(
        school_fk=school_a, student_fk=child_a, care_session="AM",
    )
    assert stored_am.handoff_recipient_id == staff_a.pk
    assert stored_am.handoff_verified is True

    replay = client_a.post(CHECKOUT, {
        "student_id": str(child_a.pk), "care_session": "PM",
        "pickup_contact_id": contact.pk, "pickup_verified": True,
    }, format="json")
    assert replay.status_code == 400
    assert AftercareAttendance.objects.filter(school_fk=school_a).count() == 2
    assert AftercareAttendance.objects.filter(school_fk=school_b).count() == 0

    # A separate signed tenant may begin custody of its own child, not A's.
    clock[0] = datetime(2025, 9, 3, 12, 0, tzinfo=dt_timezone.utc)
    own = client_b.post(CHECKIN, {
        "student_id": str(child_b.pk), "care_session": "AM",
    }, format="json")
    assert own.status_code == 201, getattr(own, "data", None)
    assert _row(client_b.get(ROSTER, {"care_session": "AM"}), child_b)["attendance"]["checkin_time"]
    assert AftercareAttendance.objects.filter(school_fk=school_b).count() == 1
    assert AftercareAttendance.objects.filter(school_fk=school_a).count() == 2

    # Previously issued staff bearers must lose all custody authority on revocation.
    staff_a.is_active = False
    staff_a.save(update_fields=["is_active"])
    assert client_a.get(ROSTER, {"care_session": "AM"}).status_code in (401, 403)
    assert client_a.post(CHECKIN, {
        "student_id": str(child_a.pk), "care_session": "PM",
    }, format="json").status_code in (401, 403)
    assert AftercareAttendance.objects.filter(school_fk=school_a).count() == 2
