# backend/athletics/tests/test_persistent_rbac.py
from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from athletics.models import Event, Season, Sport, Team, TeamCoach
from core.models import School, UserRole

User = get_user_model()
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
pytestmark = pytest.mark.django_db


def _school(name):
    return School.objects.create(name=name)


def _user(prefix, school, *, is_staff=False):
    user = User.objects.create_user(
        username=f"{prefix}_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        is_staff=is_staff,
    )
    UserRole.objects.create(
        user=user,
        school=school,
        role_code=f"{prefix}_{uuid.uuid4().hex[:8]}",
    )
    return user


def _client(user, school, *, role_header=None):
    client = APIClient()
    client.force_authenticate(user=user)
    credentials = {"HTTP_X_SCHOOL_ID": str(school.id)}
    if role_header is not None:
        credentials["HTTP_X_ROLE"] = role_header
    client.credentials(**credentials)
    return client


def _team(school, suffix):
    sport = Sport.objects.create(school=school, name=f"Soccer {suffix}")
    season = Season.objects.create(
        school=school,
        name=f"Fall {suffix}",
        start_date=date(2026, 8, 1),
        end_date=date(2026, 11, 30),
    )
    return Team.objects.create(
        school=school,
        sport=sport,
        season=season,
        display_name=f"Varsity {suffix}",
    )


def _event_payload(team):
    return {
        "team": team.id,
        "facility": None,
        "event_type": "PRACTICE",
        "title": "Practice",
        "starts_at": "2026-08-20T18:00:00Z",
        "ends_at": "2026-08-20T20:00:00Z",
        "opponent": "",
        "is_home": True,
        "notes": "",
    }


def test_director_role_header_cannot_create_authority():
    school = _school("Header Director")
    user = _user("header_director", school)
    response = _client(user, school, role_header="athletic_director").get(
        "/api/athletics/sports/"
    )
    assert response.status_code == 403


def test_coach_role_header_cannot_create_authority():
    school = _school("Header Coach")
    user = _user("header_coach", school)
    response = _client(user, school, role_header="coach").get(
        "/api/athletics/events/"
    )
    assert response.status_code == 403


def test_django_staff_flag_cannot_bypass_crown_athletics_permission():
    school = _school("Staff Only")
    user = _user("staff_only", school, is_staff=True)
    response = _client(user, school).get("/api/athletics/sports/")
    assert response.status_code == 403


def test_inactive_same_school_coach_assignment_does_not_create_authority():
    school = _school("Inactive Coach")
    user = _user("inactive_coach", school)
    team = _team(school, "Inactive")
    TeamCoach.objects.create(
        school=school,
        team=team,
        user=user,
        is_active=False,
    )
    response = _client(user, school).get("/api/athletics/events/")
    assert response.status_code == 403


def test_other_school_coach_assignment_does_not_create_authority():
    requested_school = _school("Requested School")
    assigned_school = _school("Assigned School")
    user = _user("cross_school_coach", requested_school)
    team = _team(assigned_school, "Other School")
    TeamCoach.objects.create(
        school=assigned_school,
        team=team,
        user=user,
        is_active=True,
    )
    response = _client(user, requested_school).get("/api/athletics/events/")
    assert response.status_code == 403


def test_coach_can_create_event_for_actively_assigned_team():
    school = _school("Assigned Create")
    user = _user("assigned_create", school)
    team = _team(school, "Assigned Create")
    TeamCoach.objects.create(school=school, team=team, user=user, is_active=True)

    response = _client(user, school).post(
        "/api/athletics/events/", _event_payload(team), format="json"
    )

    assert response.status_code == 201
    assert Event.objects.filter(school=school, team=team, title="Practice").exists()


def test_coach_cannot_create_event_for_unassigned_team():
    school = _school("Unassigned Create")
    user = _user("unassigned_create", school)
    assigned_team = _team(school, "Assigned")
    unassigned_team = _team(school, "Unassigned")
    TeamCoach.objects.create(school=school, team=assigned_team, user=user, is_active=True)

    response = _client(user, school).post(
        "/api/athletics/events/", _event_payload(unassigned_team), format="json"
    )

    assert response.status_code == 403
    assert not Event.objects.filter(school=school, team=unassigned_team).exists()


def test_coach_cannot_reassign_event_to_unassigned_team():
    school = _school("Unassigned Reassign")
    user = _user("unassigned_reassign", school)
    assigned_team = _team(school, "Assigned Reassign")
    unassigned_team = _team(school, "Unassigned Reassign")
    TeamCoach.objects.create(school=school, team=assigned_team, user=user, is_active=True)
    event = Event.objects.create(
        school=school,
        team=assigned_team,
        event_type="PRACTICE",
        title="Original Practice",
        starts_at="2026-08-20T18:00:00Z",
        ends_at="2026-08-20T20:00:00Z",
    )

    response = _client(user, school).patch(
        f"/api/athletics/events/{event.id}/",
        {"team": unassigned_team.id},
        format="json",
    )

    assert response.status_code == 403
    event.refresh_from_db()
    assert event.team_id == assigned_team.id
