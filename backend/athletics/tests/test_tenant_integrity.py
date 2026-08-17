from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient

from athletics.models import AthleteClearance, Facility, Season, Sport, Team
from core.models import CrownPermission, Family, RolePermission, School, Student, UserRole

User = get_user_model()
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
pytestmark = pytest.mark.django_db


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _student(school: School, suffix: str) -> Student:
    family = Family.objects.create(school=school, family_name=f"Family {suffix}")
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"S-{suffix}-{uuid.uuid4().hex[:6]}",
        first_name="Test",
        last_name="Student",
        dob=date(2010, 1, 1),
        status="ACTIVE",
    )


def _sport(school: School, suffix: str) -> Sport:
    return Sport.objects.create(school=school, name=f"Soccer {suffix}")


def _season(school: School, suffix: str) -> Season:
    return Season.objects.create(
        school=school,
        name=f"Fall {suffix}",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 11, 30),
    )


def _team(school: School, suffix: str) -> Team:
    return Team.objects.create(
        school=school,
        sport=_sport(school, suffix),
        season=_season(school, suffix),
        display_name=f"Varsity {suffix}",
    )


def _director(school: School):
    user = User.objects.create_user(
        username=f"ath_dir_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
    )
    role_code = f"ath_dir_{uuid.uuid4().hex[:8]}"
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(code="athletics.view")
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)
    return user


def _client(user, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _director_client(school: School) -> APIClient:
    return _client(_director(school), school)


def test_team_rejects_foreign_sport():
    school = _school("Team School")
    foreign = _school("Foreign Sport School")
    response = _director_client(school).post(
        "/api/athletics/teams/",
        {
            "sport_id": _sport(foreign, "Foreign").id,
            "season_id": _season(school, "Local").id,
            "display_name": "Varsity",
            "level": "V",
        },
        format="json",
    )
    assert response.status_code == 400
    assert Team.objects.filter(school=school).count() == 0


def test_team_rejects_foreign_season():
    school = _school("Season Team School")
    foreign = _school("Foreign Season School")
    response = _director_client(school).post(
        "/api/athletics/teams/",
        {
            "sport_id": _sport(school, "Local").id,
            "season_id": _season(foreign, "Foreign").id,
            "display_name": "Varsity",
            "level": "V",
        },
        format="json",
    )
    assert response.status_code == 400
    assert Team.objects.filter(school=school).count() == 0


def test_team_coach_rejects_foreign_team():
    school = _school("Coach Team School")
    foreign = _school("Foreign Coach Team")
    coach = User.objects.create_user(
        username=f"coach_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
    )
    response = _director_client(school).post(
        "/api/athletics/coaches/",
        {"team": str(_team(foreign, "Foreign").id), "user": str(coach.id)},
        format="json",
    )
    assert response.status_code == 400


def test_team_coach_rejects_foreign_user():
    school = _school("Coach User School")
    foreign = _school("Foreign Coach User")
    coach = User.objects.create_user(
        username=f"foreign_coach_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=foreign,
    )
    response = _director_client(school).post(
        "/api/athletics/coaches/",
        {"team": str(_team(school, "Local").id), "user": str(coach.id)},
        format="json",
    )
    assert response.status_code == 400


def test_team_coach_accepts_single_role_school_membership_when_direct_school_unset():
    school = _school("Role Membership School")
    coach = User.objects.create_user(
        username=f"role_coach_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=None,
    )
    UserRole.objects.create(
        user=coach,
        school=school,
        role_code=f"coach_{uuid.uuid4().hex[:8]}",
    )
    response = _director_client(school).post(
        "/api/athletics/coaches/",
        {"team": str(_team(school, "Role").id), "user": str(coach.id)},
        format="json",
    )
    assert response.status_code == 201


def test_team_roster_rejects_foreign_student():
    school = _school("Roster School")
    foreign = _school("Foreign Roster Student")
    response = _director_client(school).post(
        "/api/athletics/rosters/",
        {
            "team": str(_team(school, "Roster").id),
            "student": str(_student(foreign, "FOREIGN").id),
        },
        format="json",
    )
    assert response.status_code == 400


def test_event_rejects_foreign_team_and_foreign_facility():
    school = _school("Event School")
    foreign = _school("Foreign Event School")
    client = _director_client(school)
    now = timezone.now()

    foreign_team_response = client.post(
        "/api/athletics/events/",
        {
            "team": str(_team(foreign, "Foreign").id),
            "event_type": "GAME",
            "title": "Foreign Team",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )
    assert foreign_team_response.status_code == 400

    local_team = _team(school, "Local")
    foreign_facility = Facility.objects.create(school=foreign, name="Foreign Gym")
    foreign_facility_response = client.post(
        "/api/athletics/events/",
        {
            "team": str(local_team.id),
            "facility": str(foreign_facility.id),
            "event_type": "GAME",
            "title": "Foreign Facility",
            "starts_at": (now + timedelta(days=2)).isoformat(),
            "ends_at": (now + timedelta(days=2, hours=2)).isoformat(),
        },
        format="json",
    )
    assert foreign_facility_response.status_code == 400


def test_event_same_school_relations_remain_allowed():
    school = _school("Local Event School")
    team = _team(school, "Local")
    facility = Facility.objects.create(school=school, name="Local Gym")
    now = timezone.now()
    response = _director_client(school).post(
        "/api/athletics/events/",
        {
            "team": str(team.id),
            "facility": str(facility.id),
            "event_type": "PRACTICE",
            "title": "Local Practice",
            "starts_at": (now + timedelta(days=1)).isoformat(),
            "ends_at": (now + timedelta(days=1, hours=2)).isoformat(),
        },
        format="json",
    )
    assert response.status_code == 201


def test_clearance_foreign_student_is_not_disclosed_or_created():
    requested = _school("Requested Clearance School")
    foreign = _school("Foreign Clearance School")
    student = _student(foreign, "FOREIGN-CLEARANCE")
    response = _director_client(requested).get(f"/api/athletics/clearance/{student.id}/")
    assert response.status_code == 404
    assert not AthleteClearance.objects.filter(student=student).exists()


def test_clearance_malformed_cross_school_record_is_not_returned_or_reassigned():
    school = _school("Clearance Student School")
    foreign = _school("Malformed Clearance School")
    student = _student(school, "MALFORMED")
    clearance = AthleteClearance.objects.create(school=foreign, student=student)

    response = _director_client(school).get(f"/api/athletics/clearance/{student.id}/")
    assert response.status_code == 404
    clearance.refresh_from_db()
    assert clearance.school_id == foreign.id


def test_clearance_same_school_auto_create_and_patch_preserve_student():
    school = _school("Local Clearance School")
    student = _student(school, "LOCAL-CLEARANCE")
    client = _director_client(school)

    response = client.get(f"/api/athletics/clearance/{student.id}/")
    assert response.status_code == 200
    clearance = AthleteClearance.objects.get(student=student)
    assert clearance.school_id == school.id

    foreign = _school("Foreign Patch Student School")
    foreign_student = _student(foreign, "FOREIGN-PATCH")
    patch = client.patch(
        f"/api/athletics/clearance/{student.id}/",
        {"student": str(foreign_student.id), "insurance_on_file": True},
        format="json",
    )
    assert patch.status_code == 400
    clearance.refresh_from_db()
    assert clearance.student_id == student.id
    assert clearance.school_id == school.id
