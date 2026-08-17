import pytest
from django.db import IntegrityError, transaction
from django.utils import timezone

from aftercare.models import AftercareAttendance, AftercareEnrollment
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
    )


def test_attendance_is_scoped_by_canonical_school_and_student():
    school1 = School.objects.create(name="School 1")
    school2 = School.objects.create(name="School 2")
    student1 = _student(school1, "One")
    student2 = _student(school2, "Two")
    day = timezone.now().date()

    AftercareAttendance.objects.create(
        school_fk=school1, student_fk=student1, date=day, checkin_time=timezone.now()
    )
    AftercareAttendance.objects.create(
        school_fk=school2, student_fk=student2, date=day, checkin_time=timezone.now()
    )

    assert AftercareAttendance.objects.filter(school_fk=school1, student_fk=student1).count() == 1
    assert AftercareAttendance.objects.filter(school_fk=school2, student_fk=student2).count() == 1
    assert AftercareAttendance.objects.filter(school_fk=school1, student_fk=student2).count() == 0


def test_attendance_duplicate_same_canonical_student_day_raises():
    school = School.objects.create(name="Unique School")
    student = _student(school, "Unique")
    day = timezone.now().date()
    AftercareAttendance.objects.create(
        school_fk=school, student_fk=student, date=day, checkin_time=timezone.now()
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            AftercareAttendance.objects.create(
                school_fk=school, student_fk=student, date=day, checkin_time=timezone.now()
            )


def test_enrollment_queries_do_not_cross_tenants():
    from datetime import date

    school1 = School.objects.create(name="Enrollment School 1")
    school2 = School.objects.create(name="Enrollment School 2")
    student1 = _student(school1, "Enrollment1")
    student2 = _student(school2, "Enrollment2")
    AftercareEnrollment.objects.create(
        school_fk=school1,
        student_fk=student1,
        start_date=date(2026, 1, 1),
        billing_model="FLAT_MONTHLY",
        days_of_week=["MON"],
    )
    AftercareEnrollment.objects.create(
        school_fk=school2,
        student_fk=student2,
        start_date=date(2026, 1, 1),
        billing_model="FLAT_MONTHLY",
        days_of_week=["MON"],
    )
    assert AftercareEnrollment.objects.filter(school_fk=school1, student_fk=student1).count() == 1
    assert AftercareEnrollment.objects.filter(school_fk=school1, student_fk=student2).count() == 0
