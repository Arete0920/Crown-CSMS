"""DB-backed enrollment trust-boundary and capacity regressions for synthetic children."""
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


def _student(school, suffix):
    family = Household.objects.create(school_id=school.id, name=f"Synthetic Family {suffix}")
    child = Student.objects.create(
        school_id=school.id, household=family,
        first_name="Synthetic", last_name=suffix, grade_level="4",
    )
    return child


def _session(school):
    program = SummerCampProgram.objects.create(school=school, name="Verified Camp Program")
    return SummerCampSession.objects.create(
        school=school, program=program, name="Week One",
        start_date=date(2026, 6, 1), end_date=date(2026, 6, 5),
        start_time=time(8, 0), end_time=time(16, 0),
        status="PUBLISHED", capacity=1, waitlist_capacity=1,
    )


def test_registration_cannot_attach_another_schools_child_or_household():
    school = School.objects.create(name="Camp Scope One")
    foreign = School.objects.create(name="Camp Scope Two")
    child = _student(school, "Own")
    wrong_child = _student(foreign, "Foreign")
    session = _session(school)

    for student_id, household_id in (
        (wrong_child.id, wrong_child.household_id),
        (child.id, wrong_child.household_id),
        (None, child.household_id),
    ):
        with pytest.raises(ValueError, match="Camper|household"):
            enroll_camper(school.id, student_id, session.id, {"household_id": household_id})
        assert SummerCampEnrollment.objects.filter(school=school).count() == 0

    with pytest.raises(ValueError, match="unavailable"):
        enroll_camper(foreign.id, wrong_child.id, session.id, {})
    assert SummerCampEnrollment.objects.count() == 0


def test_duplicate_registration_and_waitlist_capacity_fail_closed():
    school = School.objects.create(name="Camp Allocation")
    child1 = _student(school, "One")
    child2 = _student(school, "Two")
    child3 = _student(school, "Three")
    session = _session(school)

    first = enroll_camper(school.id, child1.id, session.id, {})
    assert first.status == "REGISTERED"
    assert first.household_id == child1.household_id
    with pytest.raises(ValueError, match="already registered"):
        enroll_camper(school.id, child1.id, session.id, {})
    second = enroll_camper(school.id, child2.id, session.id, {})
    assert second.status == "WAITLISTED"
    assert second.waitlist_position == 1
    with pytest.raises(ValueError, match="no remaining capacity"):
        enroll_camper(school.id, child3.id, session.id, {})
    assert SummerCampEnrollment.objects.filter(school=school).count() == 2


def test_api_rejects_foreign_child_without_creating_enrollment(monkeypatch):
    school = School.objects.create(name="Camp API Scope One")
    foreign = School.objects.create(name="Camp API Scope Foreign")
    foreign_child = _student(foreign, "External")
    session = _session(school)
    monkeypatch.setattr(api, "school_id_from_request", lambda request, required=True: school.id)
    monkeypatch.setattr(api, "_require_role", lambda request, roles: True)
    request = APIRequestFactory().post(
        "/api/v1/summer-camp/enrollments/",
        {
            "session_id": session.id,
            "student_id": str(foreign_child.id),
            "household_id": str(foreign_child.household_id),
        },
        format="json",
    )
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True, is_active=True, pk=uuid4()))
    result = api.enrollments_view(request)
    assert result.status_code == 400
    assert result.data == {"detail": "Camp registration denied: camper, session or capacity is invalid."}
    assert not SummerCampEnrollment.objects.filter(school=school).exists()
