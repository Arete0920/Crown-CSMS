"""Camp program/session tenant ownership and capacity mutation regressions.

These tests use only synthetic database records. API tests force-authenticate
a same-school principal and isolate the transport authorization boundary;
the service tests independently enforce the school IDs of persisted rows.
"""
from datetime import date, time

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import School
from summer_camp import api
from summer_camp.models import SummerCampEnrollment, SummerCampProgram, SummerCampSession
from summer_camp.services import (
    create_program, create_session, update_program, update_session,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def scope():
    own = School.objects.create(name="Camp Scope A")
    other = School.objects.create(name="Camp Scope B")
    own_program = SummerCampProgram.objects.create(school=own, name="Safe Camp")
    other_program = SummerCampProgram.objects.create(school=other, name="Foreign Camp")
    session = SummerCampSession.objects.create(
        school=own, program=own_program, name="Week One",
        start_date=date(2026, 6, 1), end_date=date(2026, 6, 5),
        start_time=time(8), end_time=time(16), status="PUBLISHED",
        capacity=2, waitlist_capacity=2,
    )
    return own, other, own_program, other_program, session


def test_program_school_ownership_cannot_be_set_or_moved(scope):
    own, other, own_program, _, _ = scope
    with pytest.raises(ValueError, match="ownership"):
        create_program(own.id, {"name": "Escaped", "school": other})
    with pytest.raises(ValueError, match="ownership"):
        update_program(own.id, own_program.id, {"school": other})
    with pytest.raises(ValueError, match="ownership"):
        update_program(own.id, own_program.id, {"school_id": str(other.id)})
    own_program.refresh_from_db()
    assert own_program.school_id == own.id
    assert not SummerCampProgram.objects.filter(school=other, name="Escaped").exists()


def test_program_same_school_update_and_create_still_work(scope):
    own, _, own_program, _, _ = scope
    created = create_program(own.id, {"school": own, "name": "Another Camp"})
    assert created.school_id == own.id
    updated = update_program(own.id, own_program.id, {"name": "Renamed"})
    assert updated.name == "Renamed" and updated.school_id == own.id


def test_session_rejects_foreign_school_or_program_before_writes(scope):
    own, other, own_program, other_program, session = scope
    values = {
        "name": "New Week", "program": other_program,
        "start_date": date(2026, 6, 8), "end_date": date(2026, 6, 12),
        "start_time": time(8), "end_time": time(16),
    }
    count = SummerCampSession.objects.count()
    with pytest.raises(ValueError, match="program"):
        create_session(own.id, values)
    with pytest.raises(ValueError, match="ownership"):
        create_session(own.id, {**values, "program": own_program, "school": other})
    with pytest.raises(ValueError, match="program"):
        update_session(own.id, session.id, {"program": other_program})
    with pytest.raises(ValueError, match="ownership"):
        update_session(own.id, session.id, {"school_id": other.id})
    session.refresh_from_db()
    assert session.school_id == own.id and session.program_id == own_program.id
    assert SummerCampSession.objects.count() == count


def test_session_capacity_never_below_placements(scope):
    own, _, _, _, session = scope
    from households.models import Household, Student
    household = Household.objects.create(school_id=own.id, name="Synthetic Seats")
    child = Student.objects.create(
        school_id=own.id, household=household,
        first_name="Synthetic", last_name="Camper", grade_level="4",
    )
    SummerCampEnrollment.objects.create(
        school=own, session=session, student=child, household=household,
        status="REGISTERED",
    )
    with pytest.raises(ValueError, match="capacity"):
        update_session(own.id, session.id, {"capacity": 0})
    with pytest.raises(ValueError, match="capacity"):
        update_session(own.id, session.id, {"waitlist_capacity": -1})
    session.refresh_from_db()
    assert session.capacity == 2 and session.waitlist_capacity == 2
    updated = update_session(own.id, session.id, {"capacity": 3})
    assert updated.capacity == 3


def test_api_cannot_attach_foreign_program_or_reassign_school(scope, monkeypatch):
    own, other, _, other_program, session = scope
    actor = get_user_model().objects.create_user(
        username="camp-scope-authorized", email="camp-scope-authorized@example.test",
        password="unused", school=own,
    )
    monkeypatch.setattr(api, "school_id_from_request", lambda _request, required=True: own.id)
    monkeypatch.setattr(api, "camp_entitlement_error", lambda _school: None)
    monkeypatch.setattr(api, "_require_role", lambda _request, _allowed: True)

    factory = APIRequestFactory()
    request = factory.post("/api/v1/summer-camp/sessions/", {
        "school": str(own.id), "program": str(other_program.id),
        "name": "Forged Week", "start_date": "2026-06-08",
        "end_date": "2026-06-12", "start_time": "08:00",
        "end_time": "16:00", "capacity": 5,
    }, format="json")
    force_authenticate(request, user=actor)
    response = api.sessions_view(request)
    assert response.status_code == 400
    assert not SummerCampSession.objects.filter(school=own, name="Forged Week").exists()

    request = factory.put(f"/api/v1/summer-camp/sessions/{session.id}/", {
        "school": str(other.id), "program": str(other_program.id),
        "name": "Week One", "start_date": "2026-06-01",
        "end_date": "2026-06-05", "start_time": "08:00",
        "end_time": "16:00", "capacity": 2,
    }, format="json")
    force_authenticate(request, user=actor)
    response = api.session_detail_view(request, session_id=session.id)
    assert response.status_code == 400
    session.refresh_from_db()
    assert session.school_id == own.id
