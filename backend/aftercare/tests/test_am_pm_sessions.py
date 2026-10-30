"""Synthetic, DB-backed AM/PM extended-care contract and release regressions."""
from datetime import datetime, date

import pytest
from django.utils import timezone

from aftercare.models import AftercareAttendance, AftercareEnrollment, AftercarePickupContact
from aftercare.services import checkin_student, checkout_student, handoff_student_to_school
from core.models import CrownPermission, RolePermission, School, Staff, UserAccount, UserRole
from households.models import Household, Student

pytestmark = pytest.mark.django_db
DAY = date(2025, 9, 3)


def at(hour, minute=0):
    return timezone.make_aware(datetime(2025, 9, 3, hour, minute))


def setup_family():
    school = School.objects.create(name="Extended Care Session Test")
    household = Household.objects.create(school_id=school.id, name="One Household")
    child = Student.objects.create(
        school_id=school.id, household=household,
        first_name="One", last_name="Child", grade_level="4",
    )
    for care_session in ("AM", "PM"):
        AftercareEnrollment.objects.create(
            school_fk=school, student_fk=child, care_session=care_session,
            start_date=date(2025, 1, 1), days_of_week=["WED"],
            billing_model="FLAT_MONTHLY",
        )
    staff = Staff.objects.create(
        school=school, first_name="Receiving", last_name="Teacher",
        email="receiver@example.test", role_type="TEACHER", status="ACTIVE",
    )
    receiver = UserAccount.objects.create_user(
        username="extended-care-receiver", password="test", school=school,
        staff=staff,
    )
    UserRole.objects.create(user=receiver, school=school, role_code="SUPPORT")
    permission, _ = CrownPermission.objects.get_or_create(code="extended_care.edit")
    RolePermission.objects.get_or_create(role_code="SUPPORT", permission=permission)
    return school, household, child, receiver


def test_one_child_has_independent_am_and_pm_attendance_and_handoff():
    school, household, child, receiver = setup_family()
    am = checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    handoff = handoff_student_to_school(school.id, child.id, receiver, when=at(8, 25))
    assert handoff.pk == am.pk
    assert handoff.handoff_verified and handoff.handoff_recipient_id == receiver.pk
    assert handoff.checkout_time == at(8, 25)
    pm = checkin_student(school.id, child.id, when=at(15, 5), care_session="PM")
    assert am.pk != pm.pk and pm.handoff_time is None
    assert child.household_id == household.pk
    assert AftercareAttendance.objects.filter(school_fk=school, student_fk=child, date=DAY).count() == 2
    contact = AftercarePickupContact.objects.create(school_fk=school, student_fk=child, name="Guardian")
    released = checkout_student(school.id, child.id, pickup_contact_id=contact.pk,
                                pickup_name_freeform="", pickup_verified=True, when=at(17, 30))
    assert released.pk == pm.pk and released.pickup_verified
    assert released.handoff_time is None


def test_pm_cannot_be_implicitly_checked_in_by_am():
    school, _household, child, receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    handoff_student_to_school(school.id, child.id, receiver, when=at(8, 15))
    contact = AftercarePickupContact.objects.create(school_fk=school, student_fk=child, name="Guardian")
    with pytest.raises(AftercareAttendance.DoesNotExist):
        checkout_student(school.id, child.id, pickup_contact_id=contact.pk,
                         pickup_name_freeform="", pickup_verified=True, when=at(17, 30))
    assert AftercareAttendance.objects.filter(school_fk=school, student_fk=child).count() == 1


def test_am_handoff_rejects_invalid_receiver_and_replay():
    school, _household, child, receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    foreign_school = School.objects.create(name="Foreign School")
    other = UserAccount.objects.create_user(username="different-receiver", password="test",
                                             school=foreign_school, is_staff=True)
    with pytest.raises(ValueError, match="this school"):
        handoff_student_to_school(school.id, child.id, other, when=at(8, 15))
    attendance = AftercareAttendance.objects.get(school_fk=school, student_fk=child)
    assert attendance.handoff_time is None
    handoff_student_to_school(school.id, child.id, receiver, when=at(8, 15))
    with pytest.raises(ValueError, match="already"):
        handoff_student_to_school(school.id, child.id, receiver, when=at(8, 20))


def test_am_checkout_denied_and_pm_legacy_default_preserved():
    school, _household, child, _receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    with pytest.raises(ValueError, match="school handoff"):
        checkout_student(school.id, child.id, pickup_contact_id=1,
                         pickup_name_freeform="", pickup_verified=True,
                         when=at(8, 15), care_session="AM")
    pm = checkin_student(school.id, child.id, when=at(15, 0))
    assert pm.care_session == "PM"


def test_absent_am_does_not_block_pm():
    school, _household, child, _receiver = setup_family()
    pm = checkin_student(school.id, child.id, when=at(15, 5), care_session="PM")
    assert pm.care_session == "PM"
    assert not AftercareAttendance.objects.filter(
        school_fk=school, student_fk=child, date=DAY, care_session="AM"
    ).exists()


def test_handoff_rejects_user_without_active_staff_assignment_or_grant():
    school, _household, child, receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    receiver.staff.status = "INACTIVE"
    receiver.staff.save(update_fields=["status"])
    with pytest.raises(ValueError, match="active school staff"):
        handoff_student_to_school(school.id, child.id, receiver, when=at(8, 15))
    attendance = AftercareAttendance.objects.get(school_fk=school, student_fk=child)
    assert attendance.handoff_time is None
    receiver.staff.status = "ACTIVE"
    receiver.staff.save(update_fields=["status"])
    UserRole.objects.filter(user=receiver, school=school).delete()
    with pytest.raises(ValueError, match="school-scoped handoff authority"):
        handoff_student_to_school(school.id, child.id, receiver, when=at(8, 15))
    attendance.refresh_from_db()
    assert attendance.handoff_time is None


def test_handoff_endpoint_refuses_to_impersonate_another_staff_member():
    from rest_framework.test import APIClient

    school, _household, child, receiver = setup_family()
    checkin_student(school.id, child.id, when=at(7, 15), care_session="AM")
    another_staff = Staff.objects.create(
        school=school, first_name="Other", last_name="Teacher",
        email="another@example.test", role_type="TEACHER", status="ACTIVE",
    )
    another = UserAccount.objects.create_user(
        username="another-handoff-staff", school=school, staff=another_staff, password="test",
    )
    client = APIClient()
    client.force_authenticate(user=receiver)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    rejected = client.post(
        "/api/v1/aftercare/attendance/school-handoff/",
        {"student_id": str(child.id), "receiving_staff_id": str(another.id)},
        format="json",
    )
    assert rejected.status_code == 400
    assert "receiving_staff_id" in rejected.data
    assert not AftercareAttendance.objects.filter(
        school_fk=school, student_fk=child, care_session="AM",
        handoff_verified=True,
    ).exists()
    accepted = client.post(
        "/api/v1/aftercare/attendance/school-handoff/",
        {"student_id": str(child.id)}, format="json",
    )
    assert accepted.status_code == 200
    attendance = AftercareAttendance.objects.get(
        school_fk=school, student_fk=child, care_session="AM",
    )
    assert attendance.handoff_recipient_id == receiver.id
    assert attendance.handoff_recipient_id != another.id
    assert attendance.handoff_verified is True


def test_completed_pm_session_cannot_be_reopened_by_duplicate_checkin():
    school, _household, child, _receiver = setup_family()
    checkin_student(school.id, child.id, when=at(15), care_session="PM")
    contact = AftercarePickupContact.objects.create(
        school_fk=school, student_fk=child, name="Authorized",
    )
    checkout_student(
        school.id, child.id, contact.pk, "", True, when=at(17, 30),
    )
    with pytest.raises(ValueError, match="already been closed"):
        checkin_student(school.id, child.id, when=at(17, 40), care_session="PM", note="override")
    attendance = AftercareAttendance.objects.get(school_fk=school, student_fk=child)
    assert attendance.notes == ""
    assert attendance.checkout_time == at(17, 30)


def test_api_prevents_overlapping_am_pm_enrollment_rows_and_duplicate_billing():
    from rest_framework.test import APIClient

    school, _household, child, receiver = setup_family()
    client = APIClient()
    client.force_authenticate(user=receiver)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    baseline = AftercareEnrollment.objects.filter(
        school_fk=school, student_fk=child, is_active=True,
    ).count()
    assert baseline == 2
    for session in ("AM", "PM"):
        denied = client.post(
            "/api/v1/aftercare/enrollments/",
            {
                "student_id": str(child.id),
                "care_session": session,
                "start_date": "2025-09-01",
                "days_of_week": ["THU"],
                "billing_model": "FLAT_MONTHLY",
                "monthly_rate": "125.00",
            },
            format="json",
        )
        assert denied.status_code == 400, denied.data
        assert "Overlapping active enrollment" in str(denied.data)
    assert AftercareEnrollment.objects.filter(school_fk=school, student_fk=child).count() == baseline


def test_api_accepts_separate_future_session_after_prior_enrollment_ends():
    from rest_framework.test import APIClient

    school, _household, child, receiver = setup_family()
    AftercareEnrollment.objects.filter(
        school_fk=school, student_fk=child, care_session="AM",
    ).update(end_date=date(2025, 9, 5))
    client = APIClient()
    client.force_authenticate(user=receiver)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    response = client.post(
        "/api/v1/aftercare/enrollments/",
        {
            "student_id": str(child.id),
            "care_session": "AM",
            "start_date": "2025-09-08",
            "days_of_week": ["MON", "WED"],
            "billing_model": "FLAT_MONTHLY",
            "monthly_rate": "90.00",
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    assert response.data["care_session"] == "AM"
    assert AftercareEnrollment.objects.filter(
        school_fk=school, student_fk=child, care_session="AM",
    ).count() == 2
