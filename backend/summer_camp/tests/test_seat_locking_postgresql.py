"""PostgreSQL-only Camp seat allocation race tests for #565.

No external payment, actual children, or hosted resources are accessed.
The real two-connection tests must run (not skip) in the existing
Diadem PostgreSQL CI safety job.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time
from threading import Event

import pytest
from django.db import close_old_connections, connection, connections, transaction

from core.models import School
from households.models import Household, Student
from summer_camp.models import SummerCampEnrollment, SummerCampProgram, SummerCampSession
from summer_camp.services import cancel_enrollment, enroll_camper, move_waitlist_if_capacity_available


def _setup_seats():
    school = School.objects.create(name="Camp locking synthetic school")
    program = SummerCampProgram.objects.create(school=school, name="Camp locks")
    session = SummerCampSession.objects.create(
        school=school, program=program, name="Week A",
        start_date=date(2026, 6, 1), end_date=date(2026, 6, 5),
        start_time=time(8), end_time=time(16), status="PUBLISHED",
        capacity=1, waitlist_capacity=3,
    )
    children = []
    for label in ("Registered", "Waitlisted", "Replacement"):
        household = Household.objects.create(school=school, name=f"Synthetic {label}")
        children.append(Student.objects.create(
            school=school, household=household, first_name="Synthetic",
            last_name=label, grade_level="4",
        ))
    registered = enroll_camper(school.id, children[0].id, session.id, {})
    waitlisted = enroll_camper(school.id, children[1].id, session.id, {})
    assert registered.status == "REGISTERED"
    assert waitlisted.status == "WAITLISTED"
    return school, session, children, registered, waitlisted


def _on_other_connection(started, completed, callback):
    close_old_connections()
    try:
        started.set()
        return callback()
    finally:
        connections.close_all()
        completed.set()


@pytest.mark.django_db(transaction=True)
def test_postgresql_camp_promotion_waits_for_session_capacity_lock():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL SELECT FOR UPDATE")
    school, session, children, registered, waitlisted = _setup_seats()
    # Create an available place without invoking cancellation's auto-promotion.
    registered.status = "CANCELLED"
    registered.save(update_fields=["status"])

    started, completed = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            SummerCampSession.objects.select_for_update().get(
                id=session.id, school_id=school.id,
            )
            future = executor.submit(
                _on_other_connection, started, completed,
                lambda: (
                    move_waitlist_if_capacity_available(school.id, session.id) is not None
                ),
            )
            assert started.wait(timeout=10)
            blocked_by_session = not completed.wait(timeout=0.5)
            # This transaction wins the freed seat while holding the session lock.
            replacement = enroll_camper(school.id, children[2].id, session.id, {})
            assert replacement.status == "REGISTERED"
        promotion_occurred = future.result(timeout=15)

    assert blocked_by_session, "Promotion read capacity without waiting on the session lock"
    assert promotion_occurred is False
    waitlisted.refresh_from_db()
    assert waitlisted.status == "WAITLISTED"
    assert SummerCampEnrollment.objects.filter(
        school=school, session=session, status="REGISTERED",
    ).count() == 1


@pytest.mark.django_db(transaction=True)
def test_postgresql_camp_cancel_uses_session_first_lock_order():
    if connection.vendor != "postgresql":
        pytest.skip("Requires real PostgreSQL SELECT FOR UPDATE")
    school, session, _children, registered, waitlisted = _setup_seats()
    started, completed = Event(), Event()
    with ThreadPoolExecutor(max_workers=1) as executor:
        with transaction.atomic():
            SummerCampSession.objects.select_for_update().get(
                id=session.id, school_id=school.id,
            )
            future = executor.submit(
                _on_other_connection, started, completed,
                lambda: cancel_enrollment(school.id, registered.id).status,
            )
            assert started.wait(timeout=10)
            blocked_by_session = not completed.wait(timeout=0.5)
        cancelled_status = future.result(timeout=15)

    assert blocked_by_session, "Cancellation locked enrollment before the session"
    assert cancelled_status == "CANCELLED"
    waitlisted.refresh_from_db()
    assert waitlisted.status == "REGISTERED"
    assert SummerCampEnrollment.objects.filter(
        school=school, session=session, status="REGISTERED",
    ).count() == 1
