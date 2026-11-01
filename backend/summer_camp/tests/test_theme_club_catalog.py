"""Camp theme-week and club/elective catalog regressions."""

from datetime import date, time
from uuid import uuid4

import pytest
from django.core.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from households.models import Household, Student
from summer_camp import api
from summer_camp.models import (
    SummerCampClub,
    SummerCampClubOffering,
    SummerCampClubSelection,
    SummerCampEnrollment,
    SummerCampProgram,
    SummerCampSession,
)
from summer_camp.services import (
    cancel_club_selection,
    create_club,
    create_club_offering,
    select_club,
)

pytestmark = pytest.mark.django_db


def _school_case(label="A"):
    school = School.objects.create(name=f"Camp Catalog {label}")
    household = Household.objects.create(school_id=school.id, name=f"Family {label}")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Camper",
        last_name=label,
        grade_level="4",
    )
    program = SummerCampProgram.objects.create(
        school=school,
        name=f"Summer Program {label}",
    )
    session = SummerCampSession.objects.create(
        school=school,
        program=program,
        name=f"Week {label}",
        theme_title="Courage",
        theme_story="A week about resilient service.",
        scripture_reference="Joshua 1:9",
        virtue_focus="Courage",
        special_event="Friday service project",
        start_date=date(2027, 6, 14),
        end_date=date(2027, 6, 18),
        start_time=time(8),
        end_time=time(16),
        capacity=20,
        waitlist_capacity=5,
        status="PUBLISHED",
    )
    enrollment = SummerCampEnrollment.objects.create(
        school=school,
        session=session,
        student=student,
        household=household,
        status="REGISTERED",
    )
    return school, household, student, session, enrollment


def _second_enrollment(school, session, label):
    household = Household.objects.create(school_id=school.id, name=f"Family {label}")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Camper",
        last_name=label,
        grade_level="5",
    )
    return SummerCampEnrollment.objects.create(
        school=school,
        session=session,
        student=student,
        household=household,
        status="REGISTERED",
    )


def _club(school, code="stem"):
    return create_club(
        school.id,
        {
            "code": code,
            "name": code.replace("-", " ").title(),
            "category": "STEM",
            "description": "Synthetic club",
        },
    )


def _offering(school, session, club, *, start=time(10), end=time(11), capacity=1, waitlist=1, weekdays=None):
    return create_club_offering(
        school.id,
        {
            "session_id": session.id,
            "club_id": club.id,
            "weekdays": weekdays or [0, 2, 4],
            "start_time": start,
            "end_time": end,
            "location": "Room 101",
            "capacity": capacity,
            "waitlist_capacity": waitlist,
            "optional_charge_cents": 2500,
            "status": "PUBLISHED",
        },
    )


def _grant(user, school, *codes):
    role = f"camp_catalog_{uuid4().hex[:12]}"
    UserRole.objects.create(user=user, school=school, role_code=role)
    for code in codes:
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role, permission=permission)


def test_session_theme_week_fields_preserve_optional_faith_context():
    school, _household, _student, session, _enrollment = _school_case("Theme")
    session.refresh_from_db()
    assert session.school_id == school.id
    assert session.theme_title == "Courage"
    assert session.scripture_reference == "Joshua 1:9"
    assert session.virtue_focus == "Courage"
    assert session.special_event == "Friday service project"

    general = SummerCampSession.objects.create(
        school=school,
        program=session.program,
        name="General Purpose Week",
        start_date=date(2027, 6, 21),
        end_date=date(2027, 6, 25),
        start_time=time(8),
        end_time=time(16),
        capacity=10,
        status="DRAFT",
    )
    assert general.theme_title == ""
    assert general.scripture_reference == ""
    assert general.virtue_focus == ""


def test_offering_rejects_cross_tenant_catalog_session_and_instructor():
    school, _h, _s, session, _e = _school_case("Home")
    foreign, _fh, _fs, foreign_session, _fe = _school_case("Foreign")
    club = _club(school)

    with pytest.raises(ValueError, match="unavailable session or catalog item"):
        create_club_offering(
            foreign.id,
            {
                "session_id": session.id,
                "club_id": club.id,
                "weekdays": [1],
                "start_time": time(9),
                "end_time": time(10),
                "capacity": 10,
                "status": "PUBLISHED",
            },
        )

    instructor = UserAccount.objects.create_user(
        username=f"foreign-instructor-{uuid4().hex[:8]}",
        password="unused",
        school=foreign,
    )
    with pytest.raises(ValidationError, match="instructor belongs to another school"):
        create_club_offering(
            school.id,
            {
                "session_id": session.id,
                "club_id": club.id,
                "instructor_id": instructor.id,
                "weekdays": [1],
                "start_time": time(9),
                "end_time": time(10),
                "capacity": 10,
                "status": "PUBLISHED",
            },
        )

    assert not SummerCampClubOffering.objects.filter(school=foreign, club=club).exists()
    assert foreign_session.school_id == foreign.id


def test_selection_serializes_capacity_waitlist_and_promotes_after_cancel():
    school, _h, _s, session, first = _school_case("Seats")
    second = _second_enrollment(school, session, "Second")
    third = _second_enrollment(school, session, "Third")
    club = _club(school, "robotics")
    offering = _offering(school, session, club, capacity=1, waitlist=1)

    selected = select_club(school.id, first.id, offering.id)
    queued = select_club(school.id, second.id, offering.id)
    assert selected.status == "ENROLLED"
    assert selected.waitlist_position is None
    assert queued.status == "WAITLISTED"
    assert queued.waitlist_position == 1

    with pytest.raises(ValueError, match="no remaining capacity"):
        select_club(school.id, third.id, offering.id)
    assert SummerCampClubSelection.objects.filter(offering=offering).count() == 2

    cancelled, promoted = cancel_club_selection(school.id, selected.id)
    queued.refresh_from_db()
    assert cancelled.status == "CANCELLED"
    assert promoted.id == queued.id
    assert queued.status == "ENROLLED"
    assert queued.waitlist_position is None


def test_selection_rejects_overlapping_schedule_but_allows_nonoverlap():
    school, _h, _s, session, enrollment = _school_case("Schedule")
    first = _offering(
        school, session, _club(school, "arts"), start=time(10), end=time(11), capacity=10, waitlist=0, weekdays=[1, 3]
    )
    overlapping = _offering(
        school, session, _club(school, "leadership"), start=time(10, 30), end=time(11, 30), capacity=10, waitlist=0, weekdays=[3]
    )
    later = _offering(
        school, session, _club(school, "service"), start=time(11), end=time(12), capacity=10, waitlist=0, weekdays=[1, 3]
    )

    assert select_club(school.id, enrollment.id, first.id).status == "ENROLLED"
    with pytest.raises(ValueError, match="conflicts"):
        select_club(school.id, enrollment.id, overlapping.id)
    assert select_club(school.id, enrollment.id, later.id).status == "ENROLLED"


def test_published_offering_requires_weekday_and_positive_capacity():
    school, _h, _s, session, _e = _school_case("Publish")
    club = _club(school, "reading")
    with pytest.raises(ValidationError, match="weekday"):
        create_club_offering(
            school.id,
            {
                "session_id": session.id,
                "club_id": club.id,
                "weekdays": [],
                "start_time": time(9),
                "end_time": time(10),
                "capacity": 5,
                "status": "PUBLISHED",
            },
        )


def test_club_api_requires_explicit_school_scoped_view_and_edit_grants(monkeypatch):
    school, _h, _s, _session, _enrollment = _school_case("Api")
    user = UserAccount.objects.create_user(
        username=f"camp-club-api-{uuid4().hex[:8]}",
        password="unused",
        school=school,
    )
    factory = APIRequestFactory()
    monkeypatch.setattr(api, "school_id_from_request", lambda request, required=True: school.id)

    denied = factory.get("/api/v1/summer-camp/clubs/")
    denied.school = school
    force_authenticate(denied, user=user)
    assert api.clubs_view(denied).status_code == 403

    _grant(user, school, "summer_camp.view")
    allowed = factory.get("/api/v1/summer-camp/clubs/")
    allowed.school = school
    force_authenticate(allowed, user=user)
    assert api.clubs_view(allowed).status_code == 200

    no_edit = factory.post(
        "/api/v1/summer-camp/clubs/",
        {"code": "stem", "name": "STEM", "category": "STEM"},
        format="json",
    )
    no_edit.school = school
    force_authenticate(no_edit, user=user)
    assert api.clubs_view(no_edit).status_code == 403

    _grant(user, school, "summer_camp.edit")
    create = factory.post(
        "/api/v1/summer-camp/clubs/",
        {"code": "stem", "name": "STEM", "category": "STEM"},
        format="json",
    )
    create.school = school
    force_authenticate(create, user=user)
    response = api.clubs_view(create)
    assert response.status_code == 201
    assert response.data["code"] == "stem"
    assert SummerCampClub.objects.filter(school=school, code="stem").count() == 1
