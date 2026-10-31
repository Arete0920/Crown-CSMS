"""Prove real migration preserves pre-existing PM attendance and permits AM on the same date."""
from datetime import date, datetime

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.utils import timezone


PRE = ("aftercare", "0006_align_canonical_index_names")
POST = ("aftercare", "0007_care_session_am_pm")


@pytest.mark.django_db(transaction=True)
def test_existing_pm_record_survives_session_unique_constraint_migration():
    executor = MigrationExecutor(connection)
    executor.migrate([PRE])
    try:
        apps = executor.loader.project_state([PRE]).apps
        School = apps.get_model("core", "School")
        Household = apps.get_model("households", "Household")
        Student = apps.get_model("households", "Student")
        Attendance = apps.get_model("aftercare", "AftercareAttendance")

        school = School.objects.create(name="Synthetic Historical PM School")
        household = Household.objects.create(school_id=school.pk, name="Historical Family")
        child = Student.objects.create(
            school_id=school.pk, household=household,
            first_name="Historic", last_name="Camper", grade_level="4",
        )
        day = date(2025, 9, 3)
        checkin = timezone.make_aware(datetime(2025, 9, 3, 15, 0))
        checkout = timezone.make_aware(datetime(2025, 9, 3, 17, 45))
        old = Attendance.objects.create(
            school_fk_id=school.pk, student_fk_id=child.pk,
            date=day, checkin_time=checkin, checkout_time=checkout,
            pickup_verified=True, late_fee_cents=750,
        )
        key = old.pk

        MigrationExecutor(connection).migrate([POST])
        current_apps = MigrationExecutor(connection).loader.project_state([POST]).apps
        SessionAttendance = current_apps.get_model("aftercare", "AftercareAttendance")
        pm = SessionAttendance.objects.get(pk=key)
        assert pm.care_session == "PM"
        assert pm.checkin_time == checkin
        assert pm.checkout_time == checkout
        assert pm.pickup_verified is True
        assert pm.late_fee_cents == 750
        assert pm.handoff_verified is False
        assert pm.handoff_time is None

        SessionAttendance.objects.create(
            school_fk_id=school.pk, student_fk_id=child.pk, date=day,
            care_session="AM", checkin_time=timezone.make_aware(datetime(2025, 9, 3, 7, 0)),
        )
        assert SessionAttendance.objects.filter(
            school_fk_id=school.pk, student_fk_id=child.pk, date=day,
        ).count() == 2
    finally:
        # Do not leave the test DB schema at an old migration after a failure.
        MigrationExecutor(connection).migrate([POST])
