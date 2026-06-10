"""
Real endpoint tests for GradeLevel — Module 1 (School / Academic Year / Grade Level).

Route: GET /api/v1/grade-levels/
ViewSet: GradeLevelViewSet (PaginatedReadOnlyViewSet)
Serializer: GradeLevelSerializer → fields: grade_level_id, school_id, code, label, sort_order

Covers:
  - Unauthenticated request denied (401/403)
  - Authenticated staff gets list scoped to own school
  - Cross-tenant isolation: school B cannot see school A's grade levels
    - Paginated response shape (total/limit/offset/results)
  - Serializer fields present and correct
  - sort_order ordering maintained
  - Single retrieve by ID
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import GradeLevel, School

pytestmark = pytest.mark.django_db
User = get_user_model()

GRADE_LEVELS_URL = "/api/v1/grade-levels/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_school(suffix=""):
    return School.objects.create(name=f"GLTest-School-{suffix or uuid.uuid4().hex[:6]}")


def _make_staff(school):
    tok = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"gl-staff-{tok}",
        email=f"gl-staff-{tok}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=True,
    )


def _make_grade_level(school, code, label, sort_order):
    return GradeLevel.objects.create(
        school=school,
        code=code,
        label=label,
        sort_order=sort_order,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGradeLevelsUnauthenticated:
    def test_list_unauthenticated_denied(self):
        """Unauthenticated GET /grade-levels/ must return 401 or 403."""
        client = APIClient()
        response = client.get(GRADE_LEVELS_URL)
        assert response.status_code in (401, 403), (
            f"Expected 401/403, got {response.status_code}"
        )

    def test_retrieve_unauthenticated_denied(self):
        """Unauthenticated GET /grade-levels/<id>/ must return 401 or 403."""
        school = _make_school()
        gl = _make_grade_level(school, "K", "Kindergarten", 1)
        client = APIClient()
        response = client.get(f"{GRADE_LEVELS_URL}{gl.id}/")
        assert response.status_code in (401, 403)


class TestGradeLevelsStaffAccess:
    def setup_method(self):
        self.school = _make_school("A")
        self.staff = _make_staff(self.school)
        self.gl_k = _make_grade_level(self.school, "K", "Kindergarten", 1)
        self.gl_1 = _make_grade_level(self.school, "1", "Grade 1", 2)
        self.gl_2 = _make_grade_level(self.school, "2", "Grade 2", 3)
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff)

    def test_list_returns_200(self):
        """Authenticated staff gets 200 on /grade-levels/."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.content}"
        )

    def test_list_returns_paginated_shape(self):
        """Response body has total/limit/offset/results keys."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data, f"No 'results' key in response: {data}"
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_list_includes_all_own_grade_levels(self):
        """Staff sees all grade levels belonging to their school."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        ids = [item["grade_level_id"] for item in response.json()["results"]]
        assert str(self.gl_k.id) in ids
        assert str(self.gl_1.id) in ids
        assert str(self.gl_2.id) in ids

    def test_serializer_fields_present(self):
        """Each result row contains the expected serializer fields."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        results = response.json()["results"]
        assert results, "No results returned"
        row = results[0]
        for field in ("grade_level_id", "school_id", "code", "label", "sort_order"):
            assert field in row, f"Field '{field}' missing from result row: {row}"

    def test_school_id_matches_tenant(self):
        """All returned grade levels carry the correct school_id."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        for row in response.json()["results"]:
            assert row["school_id"] == str(self.school.id), (
                f"school_id mismatch: expected {self.school.id}, got {row['school_id']}"
            )

    def test_ordered_by_sort_order(self):
        """Grade levels are returned in sort_order ascending order."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        sort_orders = [item["sort_order"] for item in response.json()["results"]]
        assert sort_orders == sorted(sort_orders), (
            f"Grade levels not ordered by sort_order: {sort_orders}"
        )

    def test_code_values_correct(self):
        """code field matches what was stored."""
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        codes = {item["code"] for item in response.json()["results"]}
        assert "K" in codes
        assert "1" in codes
        assert "2" in codes

    def test_retrieve_single_grade_level(self):
        """GET /grade-levels/<id>/ returns the correct grade level."""
        response = self.client.get(f"{GRADE_LEVELS_URL}{self.gl_k.id}/")
        assert response.status_code == 200
        data = response.json()
        assert data["grade_level_id"] == str(self.gl_k.id)
        assert data["code"] == "K"
        assert data["label"] == "Kindergarten"
        assert data["sort_order"] == 1


class TestGradeLevelsTenantIsolation:
    def setup_method(self):
        self.school_a = _make_school("ISO-A")
        self.school_b = _make_school("ISO-B")
        self.staff_a = _make_staff(self.school_a)
        self.staff_b = _make_staff(self.school_b)
        self.gl_a = _make_grade_level(self.school_a, "K", "Kindergarten", 1)
        self.gl_b = _make_grade_level(self.school_b, "K", "Kindergarten", 1)
        self.client = APIClient()

    def test_school_b_cannot_see_school_a_grade_levels(self):
        """Staff from school B must not see school A's grade levels."""
        self.client.force_authenticate(user=self.staff_b)
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        ids = [item["grade_level_id"] for item in response.json()["results"]]
        assert str(self.gl_a.id) not in ids, (
            "Cross-tenant leak: school B can see school A's grade level"
        )

    def test_school_a_cannot_see_school_b_grade_levels(self):
        """Staff from school A must not see school B's grade levels."""
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get(GRADE_LEVELS_URL)
        assert response.status_code == 200
        ids = [item["grade_level_id"] for item in response.json()["results"]]
        assert str(self.gl_b.id) not in ids, (
            "Cross-tenant leak: school A can see school B's grade level"
        )

    def test_header_priority_scopes_to_requested_school(self):
        """X-School-Id header takes priority and scopes the response to the requested school."""
        self.client.force_authenticate(user=self.staff_b)
        response = self.client.get(
            GRADE_LEVELS_URL,
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )
        assert response.status_code == 200
        ids = [item["grade_level_id"] for item in response.json().get("results", [])]
        assert str(self.gl_a.id) in ids, (
            "Expected X-School-Id header to scope to school A records"
        )
