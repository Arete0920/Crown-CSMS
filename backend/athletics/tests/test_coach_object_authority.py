from __future__ import annotations

import datetime as dt
import uuid

import pytest
from rest_framework.test import APIClient

from athletics.models import (
    AthleteClearance,
    AthleteEligibility,
    Season,
    Sport,
    Team,
    TeamCoach,
    TeamRoster,
)
from core.models import Family, School, Student, UserAccount, UserRole


pytestmark = pytest.mark.django_db


def _school(name: str) -> School:
    return School.objects.create(name=name)


def _user(school: School) -> UserAccount:
    user = UserAccount.objects.create_user(
        username=f"coach-object-{uuid.uuid4()}",
        password="testpass",
        school=school,
    )
    UserRole.objects.create(user=user, school=school, role_code=f"coach_{uuid.uuid4().hex[:8]}")
    return user


def _team(school: School, suffix: str) -> Team:
    sport = Sport.objects.create(school=school, name=f"Soccer {suffix}")
    season = Season.objects.create(
        school=school,
        name=f"Fall {suffix}",
        start_date=dt.date(2026, 8, 1),
        end_date=dt.date(2026, 11, 30),
    )
    return Team.objects.create(
        school=school,
        sport=sport,
        season=season,
        display_name=f"Varsity {suffix}",
    )


def _student(school: School, suffix: str) -> Student:
    family = Family.objects.create(school=school, family_name=f"Family {suffix}")
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"ATH-{suffix}-{uuid.uuid4().hex[:6]}",
        first_name="Student",
        last_name=suffix,
        dob=dt.date(2010, 1, 1),
        status="ACTIVE",
    )


def _client(user: UserAccount, school: School) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return client


def _fixture():
    school = _school("Coach object authority")
    coach = _user(school)
    assigned_team = _team(school, "Assigned")
    unassigned_team = _team(school, "Unassigned")
    assigned_student = _student(school, "Assigned")
    unassigned_student = _student(school, "Unassigned")
    TeamCoach.objects.create(school=school, team=assigned_team, user=coach, is_active=True)
    TeamRoster.objects.create(school=school, team=assigned_team, student=assigned_student)
    TeamRoster.objects.create(school=school, team=unassigned_team, student=unassigned_student)
    AthleteClearance.objects.create(school=school, student=assigned_student)
    AthleteClearance.objects.create(school=school, student=unassigned_student)
    assigned_eligibility = AthleteEligibility.objects.create(
        school=school, team=assigned_team, student=assigned_student
    )
    AthleteEligibility.objects.create(
        school=school, team=unassigned_team, student=unassigned_student
    )
    return school, coach, assigned_student, unassigned_student, assigned_eligibility


def test_coach_can_read_clearance_only_for_assigned_team_athlete():
    school, coach, assigned_student, unassigned_student, _ = _fixture()
    client = _client(coach, school)

    allowed = client.get(f"/api/athletics/clearance/{assigned_student.id}/")
    denied = client.get(f"/api/athletics/clearance/{unassigned_student.id}/")

    assert allowed.status_code == 200
    assert denied.status_code == 404


def test_coach_eligibility_list_is_limited_to_assigned_teams():
    school, coach, _, _, assigned_eligibility = _fixture()

    response = _client(coach, school).get("/api/athletics/eligibility/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == assigned_eligibility.id
