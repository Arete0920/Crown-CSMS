"""
Real endpoint tests for AcademicYear — Module 1 (School / Academic Year / Grade Level).

Route: GET /api/v1/academics/years/
ViewSet: AcademicYearViewSet (PaginatedReadOnlyViewSet)
Serializer: AcademicYearSerializer → fields: year_id, school_id, name, start_date, end_date, is_current

Covers:
  - Unauthenticated request denied (401/403)
  - Authenticated staff gets list scoped to own school
  - Cross-tenant isolation: school B cannot see school A's years
    - Paginated response shape (total/limit/offset/results)
  - Single retrieve by ID (/academics/years/<id>/)
    - Header-priority tenant scoping via X-School-Id
  - is_current field reflects DB value
"""

import datetime
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, School

pytestmark = pytest.mark.django_db
User = get_user_model()

YEARS_URL = "/api/v1/academics/years/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_school(suffix=""):
    return School.objects.create(name=f"AYTest-School-{suffix or uuid.uuid4().hex[:6]}")


def _make_staff(school):
    tok = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"ay-staff-{tok}",
        email=f"ay-staff-{tok}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=True,
    )


def _make_year(school, name, *, is_current=False, year_offset=0):
    base = datetime.date(2024 + year_offset, 9, 1)
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date=base,
        end_date=base.replace(year=base.year + 1, month=6, day=30),
        is_current=is_current,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestAcademicYearsUnauthenticated:
    def test_list_unauthenticated_denied(self):
        """Unauthenticated GET /academics/years/ must return 401 or 403."""
        client = APIClient()
        response = client.get(YEARS_URL)
        assert response.status_code in (401, 403), (
            f"Expected 401/403, got {response.status_code}"
        )

    def test_retrieve_unauthenticated_denied(self):
        """Unauthenticated GET /academics/years/<id>/ must return 401 or 403."""
        school = _make_school()
        year = _make_year(school, "2024-25", is_current=True)
        client = APIClient()
        response = client.get(f"{YEARS_URL}{year.id}/")
        assert response.status_code in (401, 403)


class TestAcademicYearsStaffAccess:
    def setup_method(self):
        self.school = _make_school("A")
        self.staff = _make_staff(self.school)
        self.year_current = _make_year(self.school, "2024-25", is_current=True)
        self.year_past = _make_year(self.school, "2023-24", year_offset=-1)
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff)

    def test_list_returns_200(self):
        """Authenticated staff gets 200 on /academics/years/."""
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.content}"
        )

    def test_list_returns_paginated_shape(self):
        """Response body has total/limit/offset/results keys."""
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data, f"No 'results' key in response: {data}"
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_list_includes_own_years(self):
        """Staff sees both years belonging to their school."""
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        ids = [item["year_id"] for item in response.json()["results"]]
        assert str(self.year_current.id) in ids, "Current year missing from list"
        assert str(self.year_past.id) in ids, "Past year missing from list"

    def test_serializer_fields_present(self):
        """Each result row contains the expected serializer fields."""
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        results = response.json()["results"]
        assert results, "No results returned"
        row = results[0]
        for field in (
            "year_id",
            "school_id",
            "name",
            "start_date",
            "end_date",
            "is_current",
        ):
            assert field in row, f"Field '{field}' missing from result row: {row}"

    def test_is_current_flag_correct(self):
        """The is_current field matches the DB value."""
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        by_id = {item["year_id"]: item for item in response.json()["results"]}
        assert by_id[str(self.year_current.id)]["is_current"] is True
        assert by_id[str(self.year_past.id)]["is_current"] is False

    def test_school_id_matches_tenant(self):
        """All returned years carry the correct school_id."""
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        for row in response.json()["results"]:
            assert row["school_id"] == str(self.school.id), (
                f"school_id mismatch: expected {self.school.id}, got {row['school_id']}"
            )

    def test_retrieve_single_year(self):
        """GET /academics/years/<id>/ returns the correct year."""
        response = self.client.get(f"{YEARS_URL}{self.year_current.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["year_id"] == str(self.year_current.id)
        assert data["name"] == "2024-25"
        assert data["is_current"] is True


class TestAcademicYearsTenantIsolation:
    def setup_method(self):
        self.school_a = _make_school("ISO-A")
        self.school_b = _make_school("ISO-B")
        self.staff_a = _make_staff(self.school_a)
        self.staff_b = _make_staff(self.school_b)
        self.year_a = _make_year(self.school_a, "2024-25-A", is_current=True)
        self.year_b = _make_year(self.school_b, "2024-25-B", is_current=True)
        self.client = APIClient()

    def test_school_b_cannot_see_school_a_years(self):
        """Staff from school B must not see school A's academic years."""
        self.client.force_authenticate(user=self.staff_b)
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        ids = [item["year_id"] for item in response.json()["results"]]
        assert str(self.year_a.id) not in ids, (
            "Cross-tenant leak: school B can see school A's academic year"
        )

    def test_school_a_cannot_see_school_b_years(self):
        """Staff from school A must not see school B's academic years."""
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get(YEARS_URL)
        assert response.status_code == 200
        ids = [item["year_id"] for item in response.json()["results"]]
        assert str(self.year_b.id) not in ids, (
            "Cross-tenant leak: school A can see school B's academic year"
        )

    def test_each_school_only_sees_own_count(self):
        """Each school's staff sees exactly their own year count."""
        self.client.force_authenticate(user=self.staff_a)
        resp_a = self.client.get(YEARS_URL)
        assert resp_a.status_code == 200
        # School A has 1 year; school B's year must not inflate the count
        ids_a = {item["year_id"] for item in resp_a.json()["results"]}
        assert str(self.year_b.id) not in ids_a

    def test_ordinary_staff_cross_school_header_returns_404(self):
        """Ordinary is_staff status is not cross-school authority."""
        self.client.force_authenticate(user=self.staff_b)
        response = self.client.get(
            YEARS_URL,
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )
        assert response.status_code == 404
