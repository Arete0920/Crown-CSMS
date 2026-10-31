"""Camp pickup authorization, audit retention, replay, and school-day regressions."""
from datetime import date, datetime, time, timezone as utc
from types import SimpleNamespace
from uuid import uuid4
import pytest
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from households.models import Household, Student
from summer_camp import api
from summer_camp.models import (
    SummerCampAttendance, SummerCampEnrollment, SummerCampPickupContact,
    SummerCampProgram, SummerCampSession, SummerCampStaffAssignment,
)
from summer_camp.services import checkin_camper, checkout_camper, verify_staff_credentials

pytestmark = pytest.mark.django_db
DAY = date(2025, 9, 3)
ARRIVAL = timezone.make_aware(datetime(2025, 9, 3, 9))
DEPARTURE = timezone.make_aware(datetime(2025, 9, 3, 15))


def _child(school, label):
    family = Household.objects.create(school_id=school.id, name=f"Family {label}")
    return Student.objects.create(school_id=school.id, household=family, first_name="Camper",
                                  last_name=label, grade_level="4")


def _session(school, label):
    program = SummerCampProgram.objects.create(school=school, name=f"Program {label}")
    return SummerCampSession.objects.create(school=school, program=program, name=f"Week {label}",
                                            start_date=DAY, end_date=DAY, start_time=time(8),
                                            end_time=time(16), capacity=12)


def _case(label):
    school = School.objects.create(name=f"Camp Release {label}")
    child, session = _child(school, label), _session(school, label)
    enrollment = SummerCampEnrollment.objects.create(school=school, session=session,
                                                     student=child, status="REGISTERED")
    attendance = SummerCampAttendance.objects.create(school=school, session=session,
                                                     student=child, date=DAY, checkin_time=ARRIVAL)
    pickup = SummerCampPickupContact.objects.create(school=school, enrollment=enrollment,
                                                    name=f"Authorized {label}")
    actor = UserAccount.objects.create_user(username=f"camp-actor-{label}", email=f"camp-actor-{label}@example.test", school=school,
                                            password="synthetic", is_staff=True)
    UserRole.objects.create(user=actor, school=school, role_code="TEACHER")
    permission, _ = CrownPermission.objects.get_or_create(code="summer_camp.edit")
    RolePermission.objects.get_or_create(role_code="TEACHER", permission=permission)
    return SimpleNamespace(school=school, child=child, session=session, enrollment=enrollment,
                           attendance=attendance, pickup=pickup, actor=actor)


def _release(c, pickup=None, *, verified=True, at=DEPARTURE, actor=None):
    return checkout_camper(c.school.id, c.child.id, c.session.id,
                           pickup_contact_id=c.pickup.id if pickup is None else pickup,
                           pickup_verified=verified, when=at,
                           verified_by=c.actor if actor is None else actor)


def _unchanged(c):
    c.attendance.refresh_from_db()
    assert (c.attendance.checkout_time, c.attendance.pickup_contact_id,
            c.attendance.pickup_verified, c.attendance.pickup_verified_by_id) == (None, None, False, None)


def test_authorized_pickup_retains_staff_audit_and_denies_replay():
    c = _case("Allowed")
    released = _release(c)
    assert released.checkout_time == DEPARTURE and released.pickup_verified
    assert released.pickup_contact_id == c.pickup.id and released.pickup_verified_by_id == c.actor.id
    with pytest.raises(ProtectedError):
        c.pickup.delete()
    alternate = SummerCampPickupContact.objects.create(school=c.school, enrollment=c.enrollment,
                                                       name="Alternate")
    with pytest.raises(ValueError, match="already been checked out"):
        _release(c, alternate.id, at=timezone.make_aware(datetime(2025, 9, 3, 15, 30)))
    c.attendance.refresh_from_db()
    assert c.attendance.pickup_contact_id == c.pickup.id and c.attendance.checkout_time == DEPARTURE
    assert c.attendance.pickup_verified_by_id == c.actor.id


def test_wrong_school_child_session_inactive_and_unverified_pickups_denied():
    c = _case("Denied")
    inactive = SummerCampPickupContact.objects.create(school=c.school, enrollment=c.enrollment,
                                                      name="Inactive", is_active=False)
    unrelated = _child(c.school, "Other")
    other = SummerCampEnrollment.objects.create(school=c.school, session=c.session,
                                                student=unrelated, status="REGISTERED")
    other_child = SummerCampPickupContact.objects.create(school=c.school, enrollment=other,
                                                         name="Other Child")
    alternate = SummerCampEnrollment.objects.create(school=c.school,
                        session=_session(c.school, "Different"), student=c.child, status="REGISTERED")
    other_session = SummerCampPickupContact.objects.create(school=c.school, enrollment=alternate,
                                                           name="Wrong Session")
    foreign = _case("Foreign").pickup
    for contact, verified, error in [
        (0, True, "active authorized"), (c.pickup.id, False, "identity must be verified"),
        (inactive.id, True, "not authorized"), (other_child.id, True, "not authorized"),
        (other_session.id, True, "not authorized"), (foreign.id, True, "not authorized"),
        (99999999, True, "not authorized"), (str(uuid4()), True, "active authorized"),
    ]:
        with pytest.raises(ValueError, match=error):
            _release(c, contact, verified=verified)
        _unchanged(c)


def test_cancelled_and_duplicate_registrations_block_release():
    c = _case("ReRegistered")
    c.enrollment.status = "CANCELLED"
    c.enrollment.save(update_fields=["status"])
    with pytest.raises(ValueError, match="One active camp registration"):
        _release(c)
    _unchanged(c)
    current = SummerCampEnrollment.objects.create(school=c.school, session=c.session,
                                                   student=c.child, status="REGISTERED")
    updated = SummerCampPickupContact.objects.create(school=c.school, enrollment=current,
                                                     name="New Authorized Contact")
    with pytest.raises(ValueError, match="not authorized"):
        _release(c)
    _unchanged(c)
    assert _release(c, updated.id).pickup_contact_id == updated.id
    duplicate = _case("Duplicate")
    SummerCampEnrollment.objects.create(school=duplicate.school, session=duplicate.session,
                                        student=duplicate.child, status="REGISTERED")
    with pytest.raises(ValueError, match="One active camp registration"):
        _release(duplicate)
    _unchanged(duplicate)


def test_missing_checkin_and_chronology_cannot_release():
    c = _case("Chronology")
    with pytest.raises(ValueError, match="precede check-in"):
        _release(c, at=timezone.make_aware(datetime(2025, 9, 3, 8, 59)))
    _unchanged(c)
    c.attendance.delete()
    with pytest.raises(ValueError, match="matching camp check-in"):
        _release(c)


def test_integer_serializer_and_api_denial_never_write(monkeypatch):
    c = _case("Serializer")
    payload = dict(session_id=c.session.id, student_id=str(c.child.id),
                   pickup_contact_id=c.pickup.id, pickup_verified=True)
    serializer = api.SummerCampAttendanceActionSerializer(data=payload)
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["pickup_contact_id"] == c.pickup.id
    invalid = api.SummerCampAttendanceActionSerializer(data={
        **payload, "pickup_contact_id": str(uuid4()),
    })
    assert not invalid.is_valid() and "pickup_contact_id" in invalid.errors
    monkeypatch.setattr(api, "school_id_from_request", lambda request, required=True: c.school.id)
    monkeypatch.setattr(api, "_require_role", lambda request, roles: True)
    request = APIRequestFactory().post("/api/v1/summer-camp/attendance/checkout/",
                                       {**payload, "pickup_verified": False}, format="json")
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_active=True, pk=uuid4()))
    response = api.attendance_checkout_view(request)
    assert response.status_code == 400
    assert response.data == {"detail": "Checkout requires a valid check-in and verified authorized pickup."}
    _unchanged(c)


def test_foreign_ungranted_inactive_and_unauthenticated_staff_denied():
    c = _case("Reviewer")
    ungranted = UserAccount.objects.create_user(username="camp-ungranted", email="camp-ungranted@example.test", school=c.school,
                                                password="synthetic", is_staff=True)
    foreign = _case("ForeignReviewer").actor
    for actor in (ungranted, foreign):
        with pytest.raises(ValueError, match="school-authorized staff verifier"):
            _release(c, actor=actor)
        _unchanged(c)
    with pytest.raises(ValueError, match="school-authorized staff verifier"):
        checkout_camper(c.school.id, c.child.id, c.session.id, pickup_contact_id=c.pickup.id,
                        pickup_verified=True, when=DEPARTURE, verified_by=None)
    _unchanged(c)
    c.actor.is_active = False
    c.actor.save(update_fields=["is_active"])
    with pytest.raises(ValueError, match="school-authorized staff verifier"):
        _release(c)
    _unchanged(c)


def test_school_civil_midnight_checkin_release_needs_approved_staff_evidence():
    c = _case("Midnight")
    c.attendance.delete()
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    c.session.status = "PUBLISHED"
    c.session.save(update_fields=["status"])
    c.enrollment.form_status, c.enrollment.health_status = "COMPLETE", "APPROVED"
    c.enrollment.payment_status, c.enrollment.balance_due_cents = "PAID_IN_FULL", 0
    c.enrollment.save(update_fields=["form_status", "health_status", "payment_status", "balance_due_cents"])
    assignment = SummerCampStaffAssignment.objects.create(school=c.school, session=c.session,
                                                           staff_user=c.actor, role="COUNSELOR")
    reviewer = UserAccount.objects.create_user(username="camp-independent-reviewer", email="camp-independent-reviewer@example.test",
                                               school=c.school, password="synthetic")
    UserRole.objects.create(user=reviewer, school=c.school, role_code="HEAD_OF_SCHOOL")
    permission, _ = CrownPermission.objects.get_or_create(code="summer_camp.edit")
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)
    verify_staff_credentials(c.school.id, assignment.id, reviewer, "synthetic-credential-proof")
    arrived = datetime(2025, 9, 3, 22, 30, tzinfo=utc.utc)
    departed = datetime(2025, 9, 4, 0, 30, tzinfo=utc.utc)
    attendance = checkin_camper(c.school.id, c.child.id, c.session.id, when=arrived)
    assert attendance.date == DAY and attendance.checkout_time is None
    release = _release(c, at=departed)
    assert release.pk == attendance.pk and release.date == DAY
    assert release.checkout_time == departed and release.pickup_contact_id == c.pickup.id
    assert release.pickup_verified_by_id == c.actor.id


def test_camp_school_local_midnight_checkout_and_replay():
    c = _case("RealLocalMidnight")
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    c.attendance.checkin_time = datetime(2025, 9, 4, 6, 55, tzinfo=utc.utc)
    c.attendance.save(update_fields=["checkin_time"])
    released_at = datetime(2025, 9, 4, 7, 5, tzinfo=utc.utc)
    from summer_camp.services import roster_today
    released = _release(c, at=released_at)
    assert released.pk == c.attendance.pk
    assert released.checkout_time == released_at
    assert released.pickup_verified_by_id == c.actor.id
    with pytest.raises(ValueError, match="already been checked out"):
        _release(c, at=released_at)


def test_multiple_open_camp_custody_records_fail_closed():
    c = _case("AmbiguousCustody")
    SummerCampAttendance.objects.create(
        school=c.school, session=c.session, student=c.child,
        date=DAY.replace(day=2), checkin_time=ARRIVAL - timezone.timedelta(days=1),
    )
    with pytest.raises(ValueError, match="Multiple open Camp custody"):
        _release(c)
    _unchanged(c)
    assert SummerCampAttendance.objects.filter(
        school=c.school, session=c.session, student=c.child,
        checkout_time__isnull=True,
    ).count() == 2


def test_old_unresolved_camp_custody_remains_visible_without_auto_release(monkeypatch):
    from summer_camp import services
    c = _case("OldCustody")
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    present = datetime(2025, 9, 8, 15, tzinfo=utc.utc)
    monkeypatch.setattr(services.timezone, "now", lambda: present)
    roster = services.roster_today(c.school.id)
    records = [row for row in roster["rows"] if row["student_id"] == str(c.child.id)]
    assert len(records) == 1
    assert records[0]["checkin_time"] is not None
    assert records[0]["requires_supervisor_reconciliation"] is True
    assert records[0]["open_custody_count"] == 1
    with pytest.raises(ValueError, match="supervisor reconciliation"):
        _release(c, at=present)
    _unchanged(c)


def test_camp_roster_uses_school_civil_date_during_utc_rollover(monkeypatch):
    from summer_camp import services
    c = _case("UtcRolloverRoster")
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    at = datetime(2025, 9, 4, 0, 30, tzinfo=utc.utc)
    monkeypatch.setattr(services.timezone, "now", lambda: at)
    roster = services.roster_today(c.school.id)
    assert roster["date"] == "2025-09-03"
    assert any(row["student_id"] == str(c.child.id) for row in roster["rows"])


def test_camp_open_custody_after_registration_cancellation_still_visible(monkeypatch):
    from summer_camp import services
    c = _case("CancelledCustody")
    c.enrollment.status = "CANCELLED"
    c.enrollment.save(update_fields=["status"])
    monkeypatch.setattr(services.timezone, "now", lambda: DEPARTURE)
    roster = services.roster_today(c.school.id)
    matching = [row for row in roster["rows"] if row["student_id"] == str(c.child.id)]
    assert len(matching) == 1
    assert matching[0]["requires_supervisor_reconciliation"] is True
    with pytest.raises(ValueError, match="One active camp registration"):
        _release(c)
    _unchanged(c)

def test_overnight_open_custody_suppresses_another_sessions_scheduled_roster():
    """A child may have a new registration without being released from yesterday."""
    from unittest.mock import patch
    from summer_camp.services import roster_today

    c = _case("CrossSessionRollover")
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    other_session = _session(c.school, "NextDay")
    other_session.start_date = date(2025, 9, 4)
    other_session.end_date = date(2025, 9, 4)
    other_session.status = "PUBLISHED"
    other_session.save(update_fields=["start_date", "end_date", "status"])
    SummerCampEnrollment.objects.create(
        school=c.school, session=other_session, student=c.child, status="REGISTERED",
    )
    current = datetime(2025, 9, 4, 17, tzinfo=utc.utc)  # 10 AM local
    with patch("summer_camp.services.timezone.now", return_value=current):
        roster = roster_today(c.school.id)

    matching = [row for row in roster["rows"] if row["student_id"] == str(c.child.id)]
    assert len(matching) == 1
    assert matching[0]["session_id"] == str(c.session.id)
    assert matching[0]["attendance_id"] == str(c.attendance.id)
    assert matching[0]["unresolved_custody"] is True
    assert matching[0]["checkout_time"] is None
    assert not any(row["session_id"] == str(other_session.id) for row in matching)

    with pytest.raises(ValueError, match="different session"):
        checkout_camper(
            c.school.id, c.child.id, other_session.id,
            pickup_contact_id=c.pickup.id, pickup_verified=True,
            when=current, verified_by=c.actor,
        )
    _unchanged(c)


def test_cancelled_enrollment_cannot_hide_unresolved_camp_child_custody():
    """No active registration must not erase an existing child custody record."""
    from unittest.mock import patch
    from summer_camp.services import roster_today

    c = _case("CancelledOpenCustody")
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    c.enrollment.status = "CANCELLED"
    c.enrollment.save(update_fields=["status"])
    current = datetime(2025, 9, 4, 17, tzinfo=utc.utc)
    with patch("summer_camp.services.timezone.now", return_value=current):
        roster = roster_today(c.school.id)

    matching = [row for row in roster["rows"] if row["attendance_id"] == str(c.attendance.id)]
    assert len(matching) == 1
    assert matching[0]["unresolved_custody"] is True
    assert matching[0]["requires_supervisor_reconciliation"] is True
    assert matching[0]["enrollment_id"] is None
    assert matching[0]["checkout_time"] is None
    _unchanged(c)


def test_inconsistent_local_custody_date_blocks_release_without_mutation():
    """Malformed historical attendance is a supervisor hold, not a free checkout."""
    c = _case("InconsistentLocalDay")
    c.school.timezone = "America/Los_Angeles"
    c.school.save(update_fields=["timezone"])
    # 00:30 UTC on Sep 4 is still Sep 3 at the school.
    c.attendance.checkin_time = datetime(2025, 9, 4, 0, 30, tzinfo=utc.utc)
    c.attendance.date = date(2025, 9, 4)  # Deliberately wrong civil date.
    c.attendance.save(update_fields=["checkin_time", "date"])
    with pytest.raises(ValueError, match="check-in date mismatch"):
        _release(c, at=datetime(2025, 9, 4, 18, tzinfo=utc.utc))
    _unchanged(c)
