"""DB-backed, synthetic Summer Camp release authorization regressions."""
from datetime import date, datetime, time, timezone as utc_timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from households.models import Household, Student
from summer_camp import api
from summer_camp.models import (
    SummerCampAttendance,
    SummerCampEnrollment,
    SummerCampPickupContact,
    SummerCampProgram,
    SummerCampSession,
    SummerCampStaffAssignment,
)
from summer_camp.services import checkin_camper, checkout_camper, verify_staff_credentials


pytestmark = pytest.mark.django_db
DAY = date(2025, 9, 3)
IN = timezone.make_aware(datetime(2025, 9, 3, 9, 0))
OUT = timezone.make_aware(datetime(2025, 9, 3, 15, 0))
EARLY = timezone.make_aware(datetime(2025, 9, 3, 8, 59))


def _student(school, suffix):
    household = Household.objects.create(school_id=school.id, name=f"Camp Family {suffix}")
    return Student.objects.create(
        school_id=school.id, household=household,
        first_name="Camper", last_name=suffix, grade_level="4",
    )


def _session(school, suffix):
    program = SummerCampProgram.objects.create(school=school, name=f"Program {suffix}")
    return SummerCampSession.objects.create(
        school=school, program=program, name=f"Session {suffix}",
        start_date=DAY, end_date=DAY,
        start_time=time(8, 0), end_time=time(16, 0),
        capacity=12,
    )


def _scenario(suffix):
    school = School.objects.create(name=f"Camp Release {suffix}")
    student = _student(school, suffix)
    session = _session(school, suffix)
    enrollment = SummerCampEnrollment.objects.create(
        school=school, session=session, student=student, status="REGISTERED")
    attendance = SummerCampAttendance.objects.create(
        school=school, session=session, student=student, date=DAY, checkin_time=IN)
    contact = SummerCampPickupContact.objects.create(
        school=school, enrollment=enrollment, name=f"Authorized {suffix}")
    verifier = UserAccount.objects.create_user(
        username=f"camp-pickup-{suffix}", email=f"camp-pickup-{suffix.lower()}@example.test", password="synthetic",
        school=school, is_staff=True,
    )
    UserRole.objects.create(user=verifier, school=school, role_code="TEACHER")
    permission, _ = CrownPermission.objects.get_or_create(code="summer_camp.edit")
    RolePermission.objects.get_or_create(role_code="TEACHER", permission=permission)
    return SimpleNamespace(
        school=school, student=student, session=session,
        enrollment=enrollment, attendance=attendance, contact=contact, verifier=verifier,
    )


def _checkout(case, *, contact_id=None, verified=True, when=OUT, verifier=None):
    return checkout_camper(
        school_id=case.school.id, session_id=case.session.id,
        student_id=case.student.id, pickup_contact_id=contact_id,
        pickup_verified=verified, when=when,
        verified_by=verifier if verifier is not None else case.verifier,
    )


def _assert_unchanged(case):
    case.attendance.refresh_from_db()
    assert case.attendance.checkout_time is None
    assert case.attendance.pickup_contact_id is None
    assert case.attendance.pickup_verified is False
    assert case.attendance.pickup_verified_by_id is None



def test_checkin_and_verified_pickup_span_utc_midnight_on_one_school_day():
    case = _scenario("BoundaryIntegrated")
    case.attendance.delete()
    case.school.timezone = "America/Los_Angeles"
    case.school.save(update_fields=["timezone"])
    case.session.status = "PUBLISHED"
    case.session.save(update_fields=["status"])
    case.enrollment.form_status = "COMPLETE"
    case.enrollment.health_status = "APPROVED"
    case.enrollment.payment_status = "PAID_IN_FULL"
    case.enrollment.balance_due_cents = 0
    case.enrollment.save(update_fields=["form_status", "health_status", "payment_status", "balance_due_cents"])
    assignment = SummerCampStaffAssignment.objects.create(
        school=case.school, session=case.session,
        staff_user=case.verifier, role="COUNSELOR",
    )
    reviewer = UserAccount.objects.create_user(
        username="camp-independent-credential-reviewer",
        school=case.school, password="synthetic",
    )
    UserRole.objects.create(user=reviewer, school=case.school, role_code="HEAD_OF_SCHOOL")
    permission, _ = CrownPermission.objects.get_or_create(code="summer_camp.edit")
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)
    verify_staff_credentials(
        case.school.id, assignment.id, reviewer, "synthetic-camp-release-credential-001",
    )
    start = datetime(2025, 9, 3, 22, 30, tzinfo=utc_timezone.utc)
    finish = datetime(2025, 9, 4, 0, 30, tzinfo=utc_timezone.utc)
    admitted = checkin_camper(case.school.id, case.student.id, case.session.id, when=start)
    assert admitted.date == DAY
    assert admitted.checkout_time is None
    released = checkout_camper(
        case.school.id, case.student.id, case.session.id,
        pickup_contact_id=case.contact.id, pickup_verified=True,
        when=finish, verified_by=case.verifier,
    )
    assert released.pk == admitted.pk
    assert released.date == DAY
    assert released.checkout_time == finish
    assert released.pickup_verified_by_id == case.verifier.id
    assert released.pickup_contact_id == case.contact.id


def test_verified_active_same_enrollment_pickup_succeeds():
    case = _scenario("Allowed")
    result = _checkout(case, contact_id=case.contact.id)
    assert result.checkout_time == OUT
    assert result.pickup_verified is True
    assert result.pickup_contact_id == case.contact.id
    assert result.pickup_verified_by_id == case.verifier.id
    case.attendance.refresh_from_db()
    assert case.attendance.pickup_contact_id == case.contact.id


def test_denied_pickups_never_write_checkout_fields():
    case = _scenario("Denied")
    inactive = SummerCampPickupContact.objects.create(
        school=case.school, enrollment=case.enrollment, name="Inactive", is_active=False)
    other_student = _student(case.school, "DifferentChild")
    other_enrollment = SummerCampEnrollment.objects.create(
        school=case.school, session=case.session, student=other_student, status="REGISTERED")
    other_child = SummerCampPickupContact.objects.create(
        school=case.school, enrollment=other_enrollment, name="Different Child")
    alternate_session = _session(case.school, "Alternate")
    alternate_enrollment = SummerCampEnrollment.objects.create(
        school=case.school, session=alternate_session, student=case.student, status="REGISTERED")
    other_session = SummerCampPickupContact.objects.create(
        school=case.school, enrollment=alternate_enrollment, name="Wrong Session")
    foreign = _scenario("Foreign").contact

    denied = [
        (None, True, "active authorized"),
        (case.contact.id, False, "identity must be verified"),
        (inactive.id, True, "not authorized"),
        (other_child.id, True, "not authorized"),
        (other_session.id, True, "not authorized"),
        (foreign.id, True, "not authorized"),
        (99999999, True, "not authorized"),
        (str(uuid4()), True, "active authorized"),
    ]
    for contact_id, verified, message in denied:
        with pytest.raises(ValueError, match=message):
            _checkout(case, contact_id=contact_id, verified=verified)
        _assert_unchanged(case)


def test_cancelled_enrollment_pickup_contact_is_invalid_after_re_registration():
    case = _scenario("ReRegister")
    case.enrollment.status = "CANCELLED"
    case.enrollment.save(update_fields=["status"])
    current = SummerCampEnrollment.objects.create(
        school=case.school, session=case.session, student=case.student, status="REGISTERED")
    current_contact = SummerCampPickupContact.objects.create(
        school=case.school, enrollment=current, name="New Authorized Contact")

    with pytest.raises(ValueError, match="not authorized"):
        _checkout(case, contact_id=case.contact.id)
    _assert_unchanged(case)

    released = _checkout(case, contact_id=current_contact.id)
    assert released.pickup_contact_id == current_contact.id
    assert released.pickup_verified_by_id == case.verifier.id


def test_checkout_denied_without_one_unique_current_registration():
    case = _scenario("NoCurrentRegistration")
    case.enrollment.status = "CANCELLED"
    case.enrollment.save(update_fields=["status"])
    with pytest.raises(ValueError, match="One active camp registration"):
        _checkout(case, contact_id=case.contact.id)
    _assert_unchanged(case)

    case.enrollment.status = "REGISTERED"
    case.enrollment.save(update_fields=["status"])
    SummerCampEnrollment.objects.create(
        school=case.school, session=case.session, student=case.student,
        status="REGISTERED",
    )
    with pytest.raises(ValueError, match="One active camp registration"):
        _checkout(case, contact_id=case.contact.id)
    _assert_unchanged(case)


def test_missing_checkin_and_chronology_denied_before_mutation():
    case = _scenario("Chronology")
    with pytest.raises(ValueError, match="precede check-in"):
        _checkout(case, contact_id=case.contact.id, when=EARLY)
    _assert_unchanged(case)
    case.attendance.delete()
    with pytest.raises(ValueError, match="matching camp check-in"):
        _checkout(case, contact_id=case.contact.id)


def test_repeated_checkout_cannot_change_contact_or_release_time():
    case = _scenario("Repeat")
    second = SummerCampPickupContact.objects.create(
        school=case.school, enrollment=case.enrollment, name="Second")
    _checkout(case, contact_id=case.contact.id)
    with pytest.raises(ValueError, match="already been checked out"):
        _checkout(case, contact_id=second.id, when=timezone.make_aware(datetime(2025, 9, 3, 15, 30)))
    case.attendance.refresh_from_db()
    assert case.attendance.pickup_contact_id == case.contact.id
    assert case.attendance.checkout_time == OUT


def test_pickup_id_serializer_matches_integer_database_key():
    case = _scenario("Serializer")
    serializer = api.SummerCampAttendanceActionSerializer(data={
        "session_id": case.session.id,
        "student_id": str(case.student.id),
        "pickup_contact_id": case.contact.id,
        "pickup_verified": True,
    })
    assert serializer.is_valid(), serializer.errors
    assert serializer.validated_data["pickup_contact_id"] == case.contact.id
    wrong_type = api.SummerCampAttendanceActionSerializer(data={
        "session_id": case.session.id,
        "student_id": str(case.student.id),
        "pickup_contact_id": str(uuid4()),
        "pickup_verified": True,
    })
    assert not wrong_type.is_valid()
    assert "pickup_contact_id" in wrong_type.errors


def test_checkout_api_returns_bounded_client_error_without_checkout_write(monkeypatch):
    case = _scenario("HttpDenied")
    monkeypatch.setattr(api, "school_id_from_request", lambda request, required=True: case.school.id)
    monkeypatch.setattr(api, "_require_role", lambda request, roles: True)
    request = APIRequestFactory().post(
        "/api/v1/summer-camp/attendance/checkout/",
        {
            "session_id": case.session.id,
            "student_id": str(case.student.id),
            "pickup_verified": False,
        },
        format="json",
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_active=True, pk=uuid4()))
    response = api.attendance_checkout_view(request)
    assert response.status_code == 400
    assert response.data == {
        "detail": "Checkout requires a valid check-in and verified authorized pickup.",
    }
    _assert_unchanged(case)


def test_release_requires_identified_active_school_scoped_staff_grant():
    case = _scenario("Verifier")
    staff_only = UserAccount.objects.create_user(
        username="camp-staff-without-grant", email="camp-staff-no-grant@example.test", school=case.school,
        password="synthetic", is_staff=True,
    )
    foreign = _scenario("UnrelatedVerifier").verifier
    for actor in (staff_only, foreign):
        with pytest.raises(ValueError, match="school-authorized staff verifier"):
            _checkout(case, contact_id=case.contact.id, verifier=actor)
        _assert_unchanged(case)

    case.verifier.is_active = False
    case.verifier.save(update_fields=["is_active"])
    with pytest.raises(ValueError, match="school-authorized staff verifier"):
        _checkout(case, contact_id=case.contact.id)
    _assert_unchanged(case)


def test_release_requires_authenticated_staff_actor_not_just_contact_id():
    case = _scenario("NoActor")
    with pytest.raises(ValueError, match="school-authorized staff verifier"):
        checkout_camper(
            school_id=case.school.id, session_id=case.session.id,
            student_id=case.student.id, pickup_contact_id=case.contact.id,
            pickup_verified=True, when=OUT, verified_by=None,
        )
    _assert_unchanged(case)


def test_completed_release_preserves_contact_and_verifier_audit():
    from django.db.models.deletion import ProtectedError

    case = _scenario("AuditRetention")
    _checkout(case, contact_id=case.contact.id)
    with pytest.raises(ProtectedError):
        case.contact.delete()
    case.attendance.refresh_from_db()
    assert case.attendance.pickup_verified
    assert case.attendance.pickup_contact_id == case.contact.id
    assert case.attendance.pickup_verified_by_id == case.verifier.id
