"""Synthetic DB-backed negative and positive Summer Camp check-in safety tests."""
from datetime import date, datetime, timedelta, time, timezone as utc_timezone

import pytest
from django.utils import timezone

from core.models import School
from households.models import Household, Student
from summer_camp.models import (
    SummerCampAttendance, SummerCampEnrollment, SummerCampFormRequirement, SummerCampPickupContact,
    SummerCampProgram, SummerCampSession, SummerCampStaffAssignment,
)
from summer_camp.services import checkin_camper, compute_camper_readiness


pytestmark = pytest.mark.django_db


@pytest.fixture
def camp_case(django_user_model):
    when = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
    school = School.objects.create(name="Safe Camp Checkin")
    other_school = School.objects.create(name="Unrelated Camp")
    household = Household.objects.create(school_id=school.id, name="Synthetic Family")
    student = Student.objects.create(
        school_id=school.id, household=household,
        first_name="Synthetic", last_name="Camper", grade_level="4",
    )
    program = SummerCampProgram.objects.create(school=school, name="Weekly Camp")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="Theme Week",
        start_date=when.date() - timedelta(days=1),
        end_date=when.date() + timedelta(days=1),
        start_time=time(8, 0), end_time=time(16, 0),
        capacity=20, status="PUBLISHED",
    )
    SummerCampFormRequirement.objects.create(
        school=school, session=session, form_type="GUARDIAN_CONSENT", required=True,
    )
    enrollment = SummerCampEnrollment.objects.create(
        school=school, session=session, student=student, household=household,
        status="REGISTERED", form_status="COMPLETE",
        health_status="APPROVED", payment_status="PAID_IN_FULL",
        balance_due_cents=0,
    )
    SummerCampPickupContact.objects.create(
        school=school, enrollment=enrollment, name="Authorized Parent", is_active=True,
    )
    staff = django_user_model.objects.create_user(
        username="synthetic-camp-checkin-staff", password="unused", school=school,
    )
    SummerCampStaffAssignment.objects.create(
        school=school, session=session, staff_user=staff, role="COUNSELOR",
    )
    return school, other_school, student, session, enrollment, when


def _admit(case):
    school, _other, student, session, _enrollment, when = case
    return checkin_camper(school.id, student.id, session.id, when=when)


def _assert_no_attendance(case):
    school, _other, student, session, _enrollment, when = case
    assert not SummerCampAttendance.objects.filter(
        school=school, student=student, session=session,
    ).exists()


def test_ready_registered_camper_admitted_once(camp_case):
    assert compute_camper_readiness(camp_case[0].id, camp_case[4].id)["status"] == "READY"
    attendance = _admit(camp_case)
    assert attendance.checkin_time == camp_case[5]
    with pytest.raises(ValueError, match="already been checked in"):
        _admit(camp_case)
    assert SummerCampAttendance.objects.filter(
        school=camp_case[0], student=camp_case[2], session=camp_case[3],
    ).count() == 1


def test_duplicate_current_registrations_are_denied_without_attendance(camp_case):
    school, _foreign, student, session, enrollment, when = camp_case
    SummerCampEnrollment.objects.create(
        school=school, session=session, student=student,
        household=enrollment.household, status="REGISTERED",
        form_status="COMPLETE", health_status="APPROVED",
        payment_status="PAID_IN_FULL", balance_due_cents=0,
    )
    with pytest.raises(ValueError, match="exactly one active registration"):
        checkin_camper(school.id, student.id, session.id, when=when)
    _assert_no_attendance(camp_case)


def test_checkin_uses_school_civil_date_across_utc_midnight(camp_case):
    school, _foreign, student, session, _enrollment, _when = camp_case
    school.timezone = "Pacific/Auckland"
    school.save(update_fields=["timezone"])
    stamp = datetime(2026, 7, 1, 23, 30, tzinfo=utc_timezone.utc)
    session.start_date = date(2026, 7, 2)
    session.end_date = date(2026, 7, 2)
    session.save(update_fields=["start_date", "end_date"])

    attendance = checkin_camper(school.id, student.id, session.id, when=stamp)
    assert attendance.date == date(2026, 7, 2)
    assert attendance.checkin_time == stamp
    assert not SummerCampAttendance.objects.filter(
        school=school, session=session, student=student, date=date(2026, 7, 1),
    ).exists()


def test_invalid_school_timezone_cannot_create_attendance(camp_case):
    school = camp_case[0]
    school.timezone = "Invalid/SchoolTimeZone"
    school.save(update_fields=["timezone"])
    with pytest.raises(ValueError, match="valid school timezone"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)


@pytest.mark.parametrize("status", ["WAITLISTED", "CANCELLED"])
def test_unregistered_state_denied_without_attendance(camp_case, status):
    enrollment = camp_case[4]
    enrollment.status = status
    enrollment.save(update_fields=["status"])
    with pytest.raises(ValueError, match="active registration"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)


@pytest.mark.parametrize("field,value", [
    ("form_status", "MISSING"),
    ("health_status", "NEEDS_REVIEW"),
    ("balance_due_cents", 100),
])
def test_recomputed_clearances_fail_closed(camp_case, field, value):
    enrollment = camp_case[4]
    setattr(enrollment, field, value)
    enrollment.save(update_fields=[field])
    with pytest.raises(ValueError, match="not cleared"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)


def test_unpublished_or_outside_dates_session_denied(camp_case):
    session = camp_case[3]
    session.status = "DRAFT"
    session.save(update_fields=["status"])
    with pytest.raises(ValueError, match="session is not available"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)
    session.status = "PUBLISHED"
    session.end_date = camp_case[5].date() - timedelta(days=1)
    session.save(update_fields=["status", "end_date"])
    with pytest.raises(ValueError, match="session is not available"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)


def test_cross_school_request_denied_without_attendance(camp_case):
    with pytest.raises(ValueError, match="session is not available"):
        checkin_camper(camp_case[1].id, camp_case[2].id, camp_case[3].id, when=camp_case[5])
    _assert_no_attendance(camp_case)


def test_removed_pickup_or_staff_clearance_denied(camp_case):
    school, _other, _student, session, enrollment, _when = camp_case
    contact = SummerCampPickupContact.objects.get(enrollment=enrollment)
    contact.is_active = False
    contact.save(update_fields=["is_active"])
    with pytest.raises(ValueError, match="not cleared"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)
    contact.is_active = True
    contact.save(update_fields=["is_active"])
    SummerCampStaffAssignment.objects.filter(school=school, session=session).delete()
    with pytest.raises(ValueError, match="not cleared"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)


def test_api_incomplete_camper_returns_400_and_never_creates_attendance(camp_case, monkeypatch):
    from types import SimpleNamespace
    from uuid import uuid4

    from rest_framework.test import APIRequestFactory, force_authenticate
    from summer_camp import api

    school, _other, student, session, enrollment, _when = camp_case
    enrollment.form_status = "MISSING"
    enrollment.save(update_fields=["form_status"])
    monkeypatch.setattr(api, "school_id_from_request", lambda request, required=True: school.id)
    monkeypatch.setattr(api, "_require_role", lambda request, roles: True)
    request = APIRequestFactory().post(
        "/api/v1/summer-camp/attendance/checkin/",
        {"session_id": session.id, "student_id": str(student.id)},
        format="json",
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_active=True, pk=uuid4()))
    response = api.attendance_checkin_view(request)
    assert response.status_code == 400
    assert response.data == {
        "detail": "Camp check-in denied: session, registration, or clearance is invalid.",
    }
    assert not SummerCampAttendance.objects.filter(school=school, session=session, student=student).exists()



def test_inactive_or_foreign_staff_does_not_satisfy_camp_ratio(camp_case):
    school, foreign_school, _student, session, _enrollment, _when = camp_case
    assignment = SummerCampStaffAssignment.objects.get(school=school, session=session)
    worker = assignment.staff_user
    worker.is_active = False
    worker.save(update_fields=["is_active"])
    with pytest.raises(ValueError, match="not cleared"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)

    worker.is_active = True
    worker.school = foreign_school
    worker.save(update_fields=["is_active", "school"])
    with pytest.raises(ValueError, match="not cleared"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)


def test_payment_pending_even_with_zero_balance_cannot_self_clear(camp_case):
    enrollment = camp_case[4]
    enrollment.payment_required_before_attendance = True
    enrollment.payment_status = "DEPOSIT_DUE"
    enrollment.save(update_fields=["payment_required_before_attendance", "payment_status"])
    with pytest.raises(ValueError, match="not cleared"):
        _admit(camp_case)
    _assert_no_attendance(camp_case)
