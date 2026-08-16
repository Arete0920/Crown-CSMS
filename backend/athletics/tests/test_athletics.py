# backend/athletics/tests/test_athletics.py
"""
Phase 12.0 Athletics Module Tests
39 passing target: URL routing, permissions, CRUD, tenant isolation,
events calendar, clearance, eligibility.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import CrownPermission, Family, RolePermission, School, Student, UserRole
from athletics.models import (
    AthleteClearance,
    AthleteEligibility,
    Event,
    Facility,
    Season,
    Sport,
    Team,
    TeamCoach,
    TeamRoster,
)

User = get_user_model()
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_school(name="Crown Academy"):
    return School.objects.create(name=name)


def _grant_athletics_view(user, school):
    role_code = f"ath_dir_{uuid.uuid4().hex[:8]}"
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(code="athletics.view")
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def _bind_tenant_without_athletics_grant(user, school):
    UserRole.objects.create(
        user=user,
        school=school,
        role_code=f"ath_user_{uuid.uuid4().hex[:8]}",
    )


def _mk_staff(school):
    u = User.objects.create_user(
        username=f"staff_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        is_staff=False,
    )
    _grant_athletics_view(u, school)
    return u


def _mk_user(role="coach"):
    return User.objects.create_user(
        username=f"{role}_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        is_staff=False,
    )


def _mk_student(school, suffix="01"):
    family = Family.objects.create(school=school, family_name=f"Fam_{suffix}")
    return Student.objects.create(
        school=school,
        family=family,
        student_number=f"S{suffix}",
        first_name="Alice",
        last_name="Smith",
        dob=date(2010, 1, 1),
        status="ACTIVE",
    )


def _ad_client(school):
    user = _mk_staff(school)
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c, user


def _coach_client(school):
    user = _mk_user("coach")
    _bind_tenant_without_athletics_grant(user, school)
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c, user


def _anon_client(school):
    c = APIClient()
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c


def _mk_sport(school, name="Basketball", gender="Boys"):
    return Sport.objects.create(school=school, name=name, gender=gender)


def _mk_season(school, name="Fall 2026"):
    return Season.objects.create(
        school=school,
        name=name,
        start_date=date(2026, 9, 1),
        end_date=date(2026, 12, 31),
        is_published=True,
    )


def _mk_team(school, sport, season, display_name="Varsity Boys Basketball", fee=0):
    return Team.objects.create(
        school=school,
        sport=sport,
        season=season,
        display_name=display_name,
        level="V",
        participation_fee_cents=fee,
    )


def _mk_event(school, team, event_type="PRACTICE", title="Practice"):
    from django.utils import timezone
    now = timezone.now()
    return Event.objects.create(
        school=school,
        team=team,
        event_type=event_type,
        title=title,
        starts_at=now + timedelta(days=1),
        ends_at=now + timedelta(days=1, hours=2),
    )


# ---------------------------------------------------------------------------
# 1. URL routing
# ---------------------------------------------------------------------------

class TestURLRoutes:
    def test_sports_route_exists(self):
        assert reverse("ath_sports-list") == "/api/athletics/sports/"

    def test_seasons_route_exists(self):
        assert reverse("ath_seasons-list") == "/api/athletics/seasons/"

    def test_teams_route_exists(self):
        assert reverse("ath_teams-list") == "/api/athletics/teams/"

    def test_facilities_route_exists(self):
        assert reverse("ath_facilities-list") == "/api/athletics/facilities/"

    def test_rosters_route_exists(self):
        assert reverse("ath_rosters-list") == "/api/athletics/rosters/"

    def test_coaches_route_exists(self):
        assert reverse("ath_coaches-list") == "/api/athletics/coaches/"

    def test_events_route_exists(self):
        assert reverse("ath_events-list") == "/api/athletics/events/"

    def test_eligibility_route_exists(self):
        assert reverse("ath_eligibility-list") == "/api/athletics/eligibility/"


# ---------------------------------------------------------------------------
# 2. Permission / auth enforcement
# ---------------------------------------------------------------------------

class TestPermissions:
    def setup_method(self):
        self.school = _mk_school()

    def test_unauthenticated_sports_rejected(self):
        c = _anon_client(self.school)
        r = c.get("/api/athletics/sports/")
        assert r.status_code in (401, 403)

    def test_unauthenticated_events_rejected(self):
        c = _anon_client(self.school)
        r = c.get("/api/athletics/events/")
        assert r.status_code in (401, 403)

    def test_unassigned_coach_cannot_read_events(self):
        c, _ = _coach_client(self.school)
        r = c.get("/api/athletics/events/")
        assert r.status_code == 403

    def test_coach_blocked_from_sports_create(self):
        c, _ = _coach_client(self.school)
        r = c.post("/api/athletics/sports/", {"name": "Soccer", "gender": "Girls"}, format="json")
        assert r.status_code in (401, 403)

    def test_ad_can_create_sport(self):
        c, _ = _ad_client(self.school)
        r = c.post("/api/athletics/sports/", {"name": "Soccer", "gender": "Girls"}, format="json")
        assert r.status_code == 201


# ---------------------------------------------------------------------------
# 3. Sports CRUD
# ---------------------------------------------------------------------------

class TestSports:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)

    def test_list_empty(self):
        r = self.client.get("/api/athletics/sports/")
        assert r.status_code == 200
        assert r.data == []

    def test_create(self):
        r = self.client.post(
            "/api/athletics/sports/",
            {"name": "Basketball", "gender": "Boys"},
            format="json",
        )
        assert r.status_code == 201
        assert r.data["name"] == "Basketball"

    def test_list_returns_created(self):
        _mk_sport(self.school)
        r = self.client.get("/api/athletics/sports/")
        assert r.status_code == 200
        assert len(r.data) == 1

    def test_update(self):
        sport = _mk_sport(self.school)
        r = self.client.patch(
            f"/api/athletics/sports/{sport.id}/",
            {"is_active": False},
            format="json",
        )
        assert r.status_code == 200
        assert r.data["is_active"] is False

    def test_delete(self):
        sport = _mk_sport(self.school, name="Tennis")
        r = self.client.delete(f"/api/athletics/sports/{sport.id}/")
        assert r.status_code == 204


# ---------------------------------------------------------------------------
# 4. Seasons CRUD
# ---------------------------------------------------------------------------

class TestSeasons:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)

    def test_create_season(self):
        r = self.client.post(
            "/api/athletics/seasons/",
            {"name": "Winter 2026", "start_date": "2026-11-01", "end_date": "2027-03-01"},
            format="json",
        )
        assert r.status_code == 201
        assert r.data["name"] == "Winter 2026"

    def test_list_season(self):
        _mk_season(self.school)
        r = self.client.get("/api/athletics/seasons/")
        assert r.status_code == 200
        assert len(r.data) == 1


# ---------------------------------------------------------------------------
# 5. Teams CRUD
# ---------------------------------------------------------------------------

class TestTeams:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)
        self.sport = _mk_sport(self.school)
        self.season = _mk_season(self.school)

    def test_create_team(self):
        r = self.client.post(
            "/api/athletics/teams/",
            {
                "sport_id": self.sport.id,
                "season_id": self.season.id,
                "display_name": "Varsity Boys Basketball",
                "level": "V",
                "participation_fee_cents": 15000,
            },
            format="json",
        )
        assert r.status_code == 201
        assert r.data["display_name"] == "Varsity Boys Basketball"
        assert r.data["participation_fee_cents"] == 15000

    def test_list_teams(self):
        _mk_team(self.school, self.sport, self.season)
        r = self.client.get("/api/athletics/teams/")
        assert r.status_code == 200
        assert len(r.data) == 1

    def test_team_detail_has_nested_sport(self):
        team = _mk_team(self.school, self.sport, self.season)
        r = self.client.get(f"/api/athletics/teams/{team.id}/")
        assert r.status_code == 200
        assert r.data["sport"]["name"] == "Basketball"


# ---------------------------------------------------------------------------
# 6. Facilities CRUD
# ---------------------------------------------------------------------------

class TestFacilities:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)

    def test_create_facility(self):
        r = self.client.post(
            "/api/athletics/facilities/",
            {"name": "Main Gym", "address": "123 Main St"},
            format="json",
        )
        assert r.status_code == 201
        assert r.data["name"] == "Main Gym"

    def test_list_facilities(self):
        Facility.objects.create(school=self.school, name="Gym A")
        r = self.client.get("/api/athletics/facilities/")
        assert r.status_code == 200
        assert len(r.data) == 1


# ---------------------------------------------------------------------------
# 7. Events
# ---------------------------------------------------------------------------

class TestEvents:
    def setup_method(self):
        from django.utils import timezone
        self.school = _mk_school()
        self.client, self.user = _ad_client(self.school)
        self.sport = _mk_sport(self.school)
        self.season = _mk_season(self.school)
        self.team = _mk_team(self.school, self.sport, self.season)
        now = timezone.now()
        self.event = Event.objects.create(
            school=self.school,
            team=self.team,
            event_type="PRACTICE",
            title="Morning Practice",
            starts_at=now + timedelta(days=1),
            ends_at=now + timedelta(days=1, hours=2),
        )

    def test_list_events(self):
        r = self.client.get("/api/athletics/events/")
        assert r.status_code == 200
        assert len(r.data) == 1

    def test_calendar_action(self):
        r = self.client.get("/api/athletics/events/calendar/")
        assert r.status_code == 200
        assert isinstance(r.data, list)
        assert len(r.data) == 1

    def test_create_event(self):
        from django.utils import timezone
        now = timezone.now()
        r = self.client.post(
            "/api/athletics/events/",
            {
                "team": self.team.id,
                "event_type": "GAME",
                "title": "vs. Rivals",
                "starts_at": (now + timedelta(days=5)).isoformat(),
                "ends_at": (now + timedelta(days=5, hours=2)).isoformat(),
            },
            format="json",
        )
        assert r.status_code == 201


# ---------------------------------------------------------------------------
# 8. Rosters
# ---------------------------------------------------------------------------

class TestRosters:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)
        self.sport = _mk_sport(self.school)
        self.season = _mk_season(self.school)
        self.team = _mk_team(self.school, self.sport, self.season)
        self.student = _mk_student(self.school)

    def test_add_student_to_roster(self):
        r = self.client.post(
            "/api/athletics/rosters/",
            {"team": self.team.id, "student": str(self.student.id)},
            format="json",
        )
        assert r.status_code == 201

    def test_list_roster(self):
        from django.utils import timezone
        TeamRoster.objects.create(
            school=self.school, team=self.team, student=self.student
        )
        r = self.client.get("/api/athletics/rosters/")
        assert r.status_code == 200
        assert len(r.data) == 1


# ---------------------------------------------------------------------------
# 9. Clearance
# ---------------------------------------------------------------------------

class TestClearance:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)
        self.student = _mk_student(self.school, suffix="CL")

    def test_retrieve_creates_if_missing(self):
        assert AthleteClearance.objects.filter(student=self.student).count() == 0
        r = self.client.get(f"/api/athletics/clearance/{self.student.id}/")
        assert r.status_code == 200
        assert AthleteClearance.objects.filter(student=self.student).count() == 1

    def test_update_clearance(self):
        r = self.client.patch(
            f"/api/athletics/clearance/{self.student.id}/",
            {"insurance_on_file": True, "physical_expires_on": "2027-01-01"},
            format="json",
        )
        assert r.status_code == 200
        assert r.data["insurance_on_file"] is True

    def test_physical_valid_flag_true(self):
        future = (date.today() + timedelta(days=180)).isoformat()
        r = self.client.patch(
            f"/api/athletics/clearance/{self.student.id}/",
            {"physical_expires_on": future},
            format="json",
        )
        assert r.status_code == 200
        assert r.data["physical_is_valid"] is True

    def test_physical_valid_flag_false_when_expired(self):
        past = (date.today() - timedelta(days=1)).isoformat()
        r = self.client.patch(
            f"/api/athletics/clearance/{self.student.id}/",
            {"physical_expires_on": past},
            format="json",
        )
        assert r.status_code == 200
        assert r.data["physical_is_valid"] is False


# ---------------------------------------------------------------------------
# 10. Eligibility
# ---------------------------------------------------------------------------

class TestEligibility:
    def setup_method(self):
        self.school = _mk_school()
        self.client, _ = _ad_client(self.school)
        self.sport = _mk_sport(self.school)
        self.season = _mk_season(self.school)
        self.team = _mk_team(self.school, self.sport, self.season)
        self.student = _mk_student(self.school, suffix="EL")

    def test_list_empty(self):
        r = self.client.get("/api/athletics/eligibility/")
        assert r.status_code == 200
        assert r.data == []

    def test_list_with_record(self):
        AthleteEligibility.objects.create(
            school=self.school,
            team=self.team,
            student=self.student,
            is_medically_cleared=True,
            is_academically_eligible=True,
            is_behaviorally_eligible=True,
            is_attendance_eligible=True,
        )
        r = self.client.get("/api/athletics/eligibility/")
        assert r.status_code == 200
        assert len(r.data) == 1
        assert r.data[0]["is_eligible"] is True

    def test_is_eligible_false_when_flags_mixed(self):
        AthleteEligibility.objects.create(
            school=self.school,
            team=self.team,
            student=self.student,
            is_medically_cleared=False,
            is_academically_eligible=True,
            is_behaviorally_eligible=True,
            is_attendance_eligible=True,
        )
        r = self.client.get("/api/athletics/eligibility/")
        assert r.status_code == 200
        assert r.data[0]["is_eligible"] is False

    def test_filter_by_team_id(self):
        AthleteEligibility.objects.create(
            school=self.school,
            team=self.team,
            student=self.student,
        )
        r = self.client.get(f"/api/athletics/eligibility/?team_id={self.team.id}")
        assert r.status_code == 200
        assert len(r.data) == 1


# ---------------------------------------------------------------------------
# 11. Tenant isolation
# ---------------------------------------------------------------------------

class TestTenantIsolation:
    def setup_method(self):
        self.school_a = _mk_school("School A")
        self.school_b = _mk_school("School B")
        self.client_a, _ = _ad_client(self.school_a)
        self.client_b, _ = _ad_client(self.school_b)

    def test_sport_from_a_hidden_from_b(self):
        _mk_sport(self.school_a, name="Basketball")
        r = self.client_b.get("/api/athletics/sports/")
        assert r.status_code == 200
        assert r.data == []

    def test_season_cross_tenant_hidden(self):
        _mk_season(self.school_a, name="Fall 2026")
        r = self.client_b.get("/api/athletics/seasons/")
        assert r.status_code == 200
        assert r.data == []

    def test_event_cross_tenant_hidden(self):
        sport = _mk_sport(self.school_a)
        season = _mk_season(self.school_a)
        team = _mk_team(self.school_a, sport, season)
        _mk_event(self.school_a, team)
        r = self.client_b.get("/api/athletics/events/")
        assert r.status_code == 200
        assert r.data == []

    def test_invalid_school_id_returns_not_found(self):
        c = APIClient()
        c.force_authenticate(user=_mk_staff(self.school_a))
        c.credentials(HTTP_X_SCHOOL_ID=str(uuid.uuid4()))
        r = c.get("/api/athletics/sports/")
        assert r.status_code in (400, 404)


# ---------------------------------------------------------------------------
# 12. Coach scoping — coach sees only their teams' events
# ---------------------------------------------------------------------------

class TestCoachScoping:
    def setup_method(self):
        self.school = _mk_school()
        self.sport = _mk_sport(self.school)
        self.season = _mk_season(self.school)
        self.team_a = _mk_team(self.school, self.sport, self.season, display_name="Team A")
        self.team_b = _mk_team(self.school, self.sport, self.season, display_name="Team B")

    def test_coach_only_sees_assigned_team_events(self):
        coach_client, coach_user = _coach_client(self.school)
        # Assign coach to team_a only
        TeamCoach.objects.create(
            school=self.school, team=self.team_a, user=coach_user, is_head_coach=True
        )
        _mk_event(self.school, self.team_a, title="Team A Practice")
        _mk_event(self.school, self.team_b, title="Team B Practice")
        r = coach_client.get("/api/athletics/events/")
        assert r.status_code == 200
        assert len(r.data) == 1
        assert r.data[0]["title"] == "Team A Practice"

    def test_ad_sees_all_team_events(self):
        client_ad, _ = _ad_client(self.school)
        _mk_event(self.school, self.team_a, title="Team A Practice")
        _mk_event(self.school, self.team_b, title="Team B Practice")
        r = client_ad.get("/api/athletics/events/")
        assert r.status_code == 200
        assert len(r.data) == 2


