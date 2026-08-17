"""Canonical extended-care service tests."""
from datetime import date, datetime

import pytest
from django.utils import timezone

from aftercare.integrations import AftercareIntegrationError
from aftercare.models import AftercareEnrollment, AftercareIncident
from aftercare.services import checkin_student, checkout_student, ensure_config, record_incident
from core.models import School
from households.models import Household, Student

pytestmark = pytest.mark.django_db


def _student(school: School, suffix: str) -> Student:
    household = Household.objects.create(school_id=school.id, name=f"Household {suffix}")
    return Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Student",
        last_name=suffix,
        grade_level="4",
    )


def _enroll(school: School, student: Student, *, days=None):
    return AftercareEnrollment.objects.create(
        school_fk=school,
        student_fk=student,
        start_date=date(2025, 1, 1),
        billing_model="FLAT_MONTHLY",
        days_of_week=days or ["MON", "TUE", "WED", "THU", "FRI"],
    )


def test_ensure_config_creates_once():
    school = School.objects.create(name="Config School")
    cfg1 = ensure_config(school_id=school.id)
    cfg2 = ensure_config(school_id=school.id)
    assert cfg1.pk == cfg2.pk
    assert cfg1.school_fk_id == school.id


def test_ensure_config_separate_schools():
    school1 = School.objects.create(name="Config School 1")
    school2 = School.objects.create(name="Config School 2")
    assert ensure_config(school1.id).pk != ensure_config(school2.id).pk


def test_checkin_requires_active_canonical_enrollment():
    school = School.objects.create(name="Checkin School")
    student = _student(school, "NoEnrollment")
    when = timezone.make_aware(datetime(2025, 9, 3, 15, 5))
    with pytest.raises(ValueError, match="actively enrolled"):
        checkin_student(school.id, student.id, when=when)


def test_checkin_creates_and_is_idempotent():
    school = School.objects.create(name="Checkin School")
    student = _student(school, "Enrolled")
    _enroll(school, student, days=["WED"])
    when = timezone.make_aware(datetime(2025, 9, 3, 15, 5))
    first = checkin_student(school.id, student.id, when=when)
    second = checkin_student(school.id, student.id, when=when)
    assert first.pk == second.pk
    assert first.school_fk_id == school.id
    assert first.student_fk_id == student.id


def test_checkout_rejects_cross_student_pickup_contact():
    from aftercare.models import AftercarePickupContact

    school = School.objects.create(name="Pickup School")
    student = _student(school, "A")
    other = _student(school, "B")
    _enroll(school, student, days=["WED"])
    _enroll(school, other, days=["WED"])
    contact = AftercarePickupContact.objects.create(
        school_fk=school,
        student_fk=other,
        name="Other Guardian",
    )
    when = timezone.make_aware(datetime(2025, 9, 3, 15, 5))
    checkin_student(school.id, student.id, when=when)
    with pytest.raises(ValueError, match="not authorized"):
        checkout_student(
            school.id,
            student.id,
            pickup_contact_id=contact.id,
            pickup_name_freeform="",
            pickup_verified=True,
            when=timezone.make_aware(datetime(2025, 9, 3, 17, 30)),
        )


def test_checkout_sets_time_without_synthetic_finance_write():
    school = School.objects.create(name="Checkout School")
    student = _student(school, "Checkout")
    _enroll(school, student, days=["WED"])
    checkin_student(
        school.id,
        student.id,
        when=timezone.make_aware(datetime(2025, 9, 3, 15, 0)),
    )
    attendance = checkout_student(
        school.id,
        student.id,
        pickup_contact_id=None,
        pickup_name_freeform="Parent",
        pickup_verified=True,
        when=timezone.make_aware(datetime(2025, 9, 3, 17, 30)),
    )
    assert attendance.checkout_time is not None
    assert attendance.late_fee_charge_id is None


def test_minor_incident_uses_canonical_student():
    school = School.objects.create(name="Incident School")
    student = _student(school, "Minor")
    incident = record_incident(school.id, student.id, "MINOR", "Scuffle")
    assert incident.school_fk_id == school.id
    assert incident.student_fk_id == student.id


def test_major_incident_fails_closed_without_verified_discipline_bridge():
    school = School.objects.create(name="Incident School")
    student = _student(school, "Major")
    with pytest.raises(AftercareIntegrationError, match="no verified canonical mapping"):
        record_incident(school.id, student.id, "MAJOR", "Serious incident")
    assert AftercareIncident.objects.filter(school_fk=school, student_fk=student).count() == 0
