"""
Real endpoint tests for School Profile — Module 1 (School / Academic Year / Grade Level).

Route: GET  /api/v1/school/
       PATCH /api/v1/school/

View: SchoolProfileView (APIView)
Serializer: SchoolSerializer → fields: school_id, name, timezone, is_active

Covers:
  - Unauthenticated request denied (401/403)
  - Authenticated staff GET returns own school profile
  - Response shape: school_id, name, timezone, is_active
  - Cross-tenant isolation: non-staff cannot retrieve a different school via X-School-Id
  - PATCH blocked for regular staff (non-superuser, non-HEAD_OF_SCHOOL) → 403
  - PATCH allowed for superuser → 200 with updated data
  - PATCH allowed for HEAD_OF_SCHOOL role holder → 200 with updated data
  - PATCH only touches writable fields (school_id and is_active are read-only)
"""

import uuid
from typing import Any

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School, UserRole

pytestmark = pytest.mark.django_db
User: Any = get_user_model()

SCHOOL_URL = "/api/v1/school/"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_school(suffix: str = ""):
    return School.objects.create(
        name=f"SPTest-School-{suffix or uuid.uuid4().hex[:6]}",
        timezone="America/New_York",
    )


def _make_staff(school: School):
    tok = uuid.uuid4().hex[:8]
    return User.objects.create_user(  # type: ignore[attr-defined]
        username=f"sp-staff-{tok}",
        email=f"sp-staff-{tok}@example.com",
        password="Passw0rd!",  # NOSONAR - test fixture only
        school=school,
        is_staff=True,
    )


def _make_regular_user(school: School):
    tok = uuid.uuid4().hex[:8]
    return User.objects.create_user(  # type: ignore[attr-defined]
        username=f"sp-user-{tok}",
        email=f"sp-user-{tok}@example.com",
        password="Passw0rd!",  # NOSONAR - test fixture only
        school=school,
        is_staff=False,
    )


def _make_superuser(school: School):
    tok = uuid.uuid4().hex[:8]
    return User.objects.create_superuser(  # type: ignore[attr-defined]
        username=f"sp-super-{tok}",
        email=f"sp-super-{tok}@example.com",
        password="Passw0rd!",  # NOSONAR - test fixture only
        school=school,
    )


def _make_head_of_school_user(school: School):
    tok = uuid.uuid4().hex[:8]
    user = User.objects.create_user(  # type: ignore[attr-defined]
        username=f"sp-head-{tok}",
        email=f"sp-head-{tok}@example.com",
        password="Passw0rd!",  # NOSONAR - test fixture only
        school=school,
        is_staff=False,
    )
    UserRole.objects.create(
        school=school,
        user=user,
        role_code="HEAD_OF_SCHOOL",
    )
    return user


# ---------------------------------------------------------------------------
# Unauthenticated tests
# ---------------------------------------------------------------------------


class TestSchoolProfileUnauthenticated:
    def test_get_unauthenticated_denied(self):
        """Unauthenticated GET /school/ must return 401 or 403."""
        client = APIClient()
        response = client.get(SCHOOL_URL)
        assert response.status_code in (401, 403), (
            f"Expected 401/403, got {response.status_code}"
        )

    def test_patch_unauthenticated_denied(self):
        """Unauthenticated PATCH /school/ must return 401 or 403."""
        client = APIClient()
        response = client.patch(SCHOOL_URL, {"name": "Hack"}, format="json")
        assert response.status_code in (401, 403), (
            f"Expected 401/403, got {response.status_code}"
        )


# ---------------------------------------------------------------------------
# Authenticated staff read tests
# ---------------------------------------------------------------------------


class TestSchoolProfileStaffAccess:
    def setup_method(self):
        self.school = _make_school("A")
        self.staff = _make_staff(self.school)
        self.client = APIClient()
        self.client.force_authenticate(user=self.staff)

    def test_get_returns_200(self):
        """Authenticated staff gets 200 on /school/."""
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.content}"
        )

    def test_get_returns_correct_school_id(self):
        """Returned school_id matches the authenticated user's school."""
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200
        data = response.json()
        assert data["school_id"] == str(self.school.id), (
            f"Expected school_id={self.school.id}, got {data.get('school_id')}"
        )

    def test_serializer_fields_present(self):
        """Response contains all expected serializer fields."""
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200
        data = response.json()
        for field in ("school_id", "name", "timezone", "is_active"):
            assert field in data, f"Field '{field}' missing from response: {data}"

    def test_name_matches_stored_value(self):
        """name field reflects the database value."""
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200
        assert response.json()["name"] == self.school.name

    def test_timezone_matches_stored_value(self):
        """timezone field reflects the database value."""
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200
        assert response.json()["timezone"] == self.school.timezone

    def test_is_active_is_boolean(self):
        """is_active field is a boolean."""
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200
        assert isinstance(response.json()["is_active"], bool)


# ---------------------------------------------------------------------------
# Tenant isolation tests
# ---------------------------------------------------------------------------


class TestSchoolProfileTenantIsolation:
    def setup_method(self):
        self.school_a = _make_school("ISO-A")
        self.school_b = _make_school("ISO-B")
        self.staff_a = _make_staff(self.school_a)
        self.regular_b = _make_regular_user(self.school_b)
        self.client = APIClient()

    def test_staff_a_gets_school_a_profile(self):
        """Staff from school A receives school A's profile."""
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get(SCHOOL_URL)
        assert response.status_code == 200
        assert response.json()["school_id"] == str(self.school_a.id)

    def test_regular_user_b_cannot_access_school_a_via_header(self):
        """Non-staff user from school B cannot retrieve school A via X-School-Id header.

        The tenant scoping layer (households/scoping.py) raises NotFound (404) for
        non-staff cross-tenant header access to avoid leaking school existence information.
        """
        self.client.force_authenticate(user=self.regular_b)
        response = self.client.get(
            SCHOOL_URL,
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )
        assert response.status_code == 404, (
            f"Expected 404 for non-staff cross-tenant access, got {response.status_code}"
        )

    def test_staff_header_override_accesses_requested_school(self):
        """Staff (is_staff=True) may use X-School-Id to view another school's profile.

        Design decision: staff-level users (is_staff=True) are permitted cross-tenant
        access via the X-School-Id header. This is the established tenant-scoping
        contract enforced in households/scoping.py (get_request_school_id) and
        mirrored in AcademicYear/GradeLevel API tests. Non-staff users are blocked
        (see test_regular_user_b_cannot_access_school_a_via_header above).
        """
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get(
            SCHOOL_URL,
            HTTP_X_SCHOOL_ID=str(self.school_b.id),
        )
        assert response.status_code == 200
        assert response.json()["school_id"] == str(self.school_b.id), (
            "Expected X-School-Id header to scope to school B"
        )


# ---------------------------------------------------------------------------
# PATCH permission tests
# ---------------------------------------------------------------------------


class TestSchoolProfilePatchPermissions:
    def setup_method(self):
        self.school = _make_school("PATCH")
        self.staff = _make_staff(self.school)
        self.superuser = _make_superuser(self.school)
        self.head_of_school = _make_head_of_school_user(self.school)
        self.client = APIClient()

    def test_patch_by_regular_staff_is_forbidden(self):
        """Regular staff (non-superuser, no HEAD_OF_SCHOOL role) PATCH returns 403."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(
            SCHOOL_URL,
            {"name": "Attempted Name Change"},
            format="json",
        )
        assert response.status_code == 403, (
            f"Expected 403 for non-admin PATCH, got {response.status_code}: {response.content}"
        )

    def test_patch_by_superuser_is_allowed(self):
        """Superuser PATCH returns 200 and updates the school name."""
        self.client.force_authenticate(user=self.superuser)
        new_name = f"Updated School {uuid.uuid4().hex[:6]}"
        response = self.client.patch(
            SCHOOL_URL,
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200, (
            f"Expected 200 for superuser PATCH, got {response.status_code}: {response.content}"
        )
        assert response.json()["name"] == new_name

    def test_patch_by_head_of_school_role_is_allowed(self):
        """HEAD_OF_SCHOOL role holder PATCH returns 200 and updates the school name."""
        self.client.force_authenticate(user=self.head_of_school)
        new_name = f"Head Updated School {uuid.uuid4().hex[:6]}"
        response = self.client.patch(
            SCHOOL_URL,
            {"name": new_name},
            format="json",
        )
        assert response.status_code == 200, (
            f"Expected 200 for HEAD_OF_SCHOOL PATCH, got {response.status_code}: {response.content}"
        )
        assert response.json()["name"] == new_name

    def test_patch_by_superuser_updates_timezone(self):
        """Superuser can update the timezone field."""
        self.client.force_authenticate(user=self.superuser)
        response = self.client.patch(
            SCHOOL_URL,
            {"timezone": "America/Chicago"},
            format="json",
        )
        assert response.status_code == 200
        assert response.json()["timezone"] == "America/Chicago"

    def test_patch_school_id_is_ignored(self):
        """school_id is read-only; attempting to change it has no effect."""
        self.client.force_authenticate(user=self.superuser)
        fake_id = str(uuid.uuid4())
        response = self.client.patch(
            SCHOOL_URL,
            {"school_id": fake_id, "name": "Legit Update"},
            format="json",
        )
        assert response.status_code == 200
        # school_id must remain unchanged
        assert response.json()["school_id"] == str(self.school.id)

    def test_patch_is_active_is_ignored(self):
        """is_active is read-only; attempting to change it has no effect."""
        self.client.force_authenticate(user=self.superuser)
        original_is_active = self.school.is_active
        response = self.client.patch(
            SCHOOL_URL,
            {"is_active": not original_is_active, "name": "Active Flag Attempt"},
            format="json",
        )
        assert response.status_code == 200
        self.school.refresh_from_db()
        assert self.school.is_active is original_is_active
        assert response.json()["is_active"] is original_is_active
