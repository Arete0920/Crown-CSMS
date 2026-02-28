import pytest
from django.utils import timezone
from aftercare.models import AftercareAttendance, AftercareEnrollment

pytestmark = pytest.mark.django_db


def test_attendance_unique_per_student_day_per_school():
    """Same student/day in different schools — both allowed; same school → IntegrityError."""
    d = timezone.now().date()
    AftercareAttendance.objects.create(school_id=1, student_id=2001, date=d, checkin_time=timezone.now())
    AftercareAttendance.objects.create(school_id=2, student_id=2001, date=d, checkin_time=timezone.now())
    assert AftercareAttendance.objects.filter(school_id=1, student_id=2001).count() == 1
    assert AftercareAttendance.objects.filter(school_id=2, student_id=2001).count() == 1


def test_attendance_duplicate_same_school_raises():
    """Same (school_id, student_id, date) → unique_together violation."""
    d = timezone.now().date()
    AftercareAttendance.objects.create(school_id=3, student_id=3001, date=d, checkin_time=timezone.now())
    with pytest.raises(Exception):
        AftercareAttendance.objects.create(school_id=3, student_id=3001, date=d, checkin_time=timezone.now())


def test_enrollment_scoped_by_school_id():
    from datetime import date
    AftercareEnrollment.objects.create(
        school_id=10, student_id=4001, start_date=date(2026, 1, 1),
        billing_model="FLAT_MONTHLY", days_of_week=["MON"]
    )
    AftercareEnrollment.objects.create(
        school_id=20, student_id=4001, start_date=date(2026, 1, 1),
        billing_model="FLAT_MONTHLY", days_of_week=["MON"]
    )
    assert AftercareEnrollment.objects.filter(school_id=10, student_id=4001).count() == 1
    assert AftercareEnrollment.objects.filter(school_id=20, student_id=4001).count() == 1
    assert AftercareEnrollment.objects.filter(school_id=99, student_id=4001).count() == 0
