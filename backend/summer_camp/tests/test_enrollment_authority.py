"""Camp registration tenant isolation, capacity, fee and authority regressions."""
from datetime import date, time
from types import SimpleNamespace
from uuid import uuid4
import pytest
from rest_framework.test import APIRequestFactory, force_authenticate
from core.models import School
from households.models import Household, Student
from summer_camp import api
from summer_camp.models import SummerCampEnrollment, SummerCampProgram, SummerCampSession
from summer_camp.services import enroll_camper
pytestmark = pytest.mark.django_db


def _child(school, label):
    household = Household.objects.create(school_id=school.id, name=f"Family {label}")
    return Student.objects.create(school_id=school.id, household=household,
                                  first_name="Synthetic", last_name=label, grade_level="4")


def _session(school):
    program = SummerCampProgram.objects.create(school=school, name="Camp Verified")
    return SummerCampSession.objects.create(
        school=school, program=program, name="Week One", start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 5), start_time=time(8), end_time=time(16),
        status="PUBLISHED", capacity=1, waitlist_capacity=1,
    )


def test_foreign_child_household_and_null_registration_denied():
    school, foreign = School.objects.create(name="Own"), School.objects.create(name="Foreign")
    own, other, session = _child(school, "Own"), _child(foreign, "Other"), _session(school)
    for child_id, family in ((other.id, other.household_id), (own.id, other.household_id),
                             (None, own.household_id)):
        with pytest.raises(ValueError, match="Camper|household"):
            enroll_camper(school.id, child_id, session.id, {"household_id": family})
        assert SummerCampEnrollment.objects.count() == 0
    with pytest.raises(ValueError, match="unavailable"):
        enroll_camper(foreign.id, other.id, session.id, {})
    assert SummerCampEnrollment.objects.count() == 0


def test_duplicates_and_waitlist_overcapacity_denied():
    school = School.objects.create(name="Camp Seats")
    first, second, third = [_child(school, name) for name in ("First", "Second", "Third")]
    session = _session(school)
    enrolled = enroll_camper(school.id, first.id, session.id, {})
    assert enrolled.status == "REGISTERED" and enrolled.household_id == first.household_id
    with pytest.raises(ValueError, match="already registered"):
        enroll_camper(school.id, first.id, session.id, {})
    queued = enroll_camper(school.id, second.id, session.id, {})
    assert queued.status == "WAITLISTED" and queued.waitlist_position == 1
    with pytest.raises(ValueError, match="no remaining capacity"):
        enroll_camper(school.id, third.id, session.id, {})
    assert SummerCampEnrollment.objects.filter(school=school).count() == 2


def test_api_denies_cross_school_registration_without_writes(monkeypatch):
    school, foreign = School.objects.create(name="API Own"), School.objects.create(name="API Foreign")
    child, session = _child(foreign, "Foreign"), _session(school)
    monkeypatch.setattr(api, "school_id_from_request", lambda request, required=True: school.id)
    monkeypatch.setattr(api, "_require_role", lambda request, roles: True)
    request = APIRequestFactory().post("/api/v1/summer-camp/enrollments/", {
        "session_id": session.id, "student_id": str(child.id),
        "household_id": str(child.household_id),
    }, format="json")
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_active=True, pk=uuid4()))
    response = api.enrollments_view(request)
    assert response.status_code == 400
    assert response.data == {"detail": "Camp registration denied: camper, session or capacity is invalid."}
    assert not SummerCampEnrollment.objects.filter(school=school).exists()


def test_client_cannot_self_certify_or_waive_payment():
    school = School.objects.create(name="Camp Intake")
    child, session = _child(school, "Intake"), _session(school)
    session.price_cents, session.deposit_cents = 12000, 2000
    session.save(update_fields=["price_cents", "deposit_cents"])
    enrollment = enroll_camper(school.id, child.id, session.id, {
        "form_status": "COMPLETE", "health_status": "APPROVED", "pickup_status": "VERIFIED",
        "payment_status": "PAID_IN_FULL", "payment_required_before_attendance": False,
        "balance_due_cents": 0,
    })
    enrollment.refresh_from_db()
    assert enrollment.form_status == "MISSING"
    assert enrollment.health_status == "NEEDS_REVIEW"
    assert enrollment.pickup_status == "MISSING"
    assert enrollment.payment_status == "DEPOSIT_DUE"
    assert enrollment.balance_due_cents == 12000
    assert enrollment.payment_required_before_attendance is True
    assert enrollment.readiness_status == "BLOCKED"


def test_serializer_rejects_clearance_assertions():
    school = School.objects.create(name="API Claims")
    child, session = _child(school, "Claim"), _session(school)
    request = api.SummerCampEnrollmentCreateSerializer(data={
        "session_id": session.id, "student_id": str(child.id),
        "health_status": "APPROVED", "payment_status": "PAID_IN_FULL",
    })
    assert not request.is_valid() and "detail" in request.errors
    assert not SummerCampEnrollment.objects.filter(school=school).exists()
