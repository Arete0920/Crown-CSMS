"""
Tests for OneRoster 1.2 CSV export endpoint.

Covers:
- Staff-only access enforcement
- Non-staff returns 403
- Unauthenticated returns 401/403
- Successful export returns multipart response with CSV files
- Missing school header rejected
- Tenant isolation: only exports data for requested school
"""
from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from academics.models import Course, Section, Term, Enrollment, AcademicYear
from core.models import School
from households.models import Household, Student

pytestmark = pytest.mark.django_db

User = get_user_model()

ONEROSTER_URL = "/api/integrations/oneroster/export/"


def _mk_school(name="Export School"):
    return School.objects.create(name=name)


def _mk_user(*, school: School, email: str, is_staff: bool = False):
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test",
        school=school,
        is_staff=is_staff,
    )


def _seed_academics(school: School):
    year = AcademicYear.objects.create(
        school=school,
        name="2026-2027",
        start_date="2026-08-15",
        end_date="2027-06-10",
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=year,
        code="2026-FALL",
        name="Fall 2026",
        active=True,
    )
    course = Course.objects.create(
        school_id=school.id,
        code="ENG-101",
        name="English I",
    )
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term="2026-FALL",
    )
    household = Household.objects.create(school_id=school.id, name="Test Family")
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Alice",
        last_name="Crown",
        grade_level="9",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    return course, section, student


def _client(user: User, school: School) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c


# ---------------------------------------------------------------------------
# Access control
# ---------------------------------------------------------------------------

class TestOneRosterAccessControl:
    def test_staff_can_export(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="staff@er.com", is_staff=True)
        _seed_academics(school)

        c = _client(staff, school)
        r = c.get(ONEROSTER_URL)
        assert r.status_code == 200

    def test_non_staff_cannot_export(self):
        school = _mk_school()
        user = _mk_user(school=school, email="plain@er.com", is_staff=False)

        c = _client(user, school)
        r = c.get(ONEROSTER_URL)
        assert r.status_code == 403

    def test_unauthenticated_cannot_export(self):
        school = _mk_school()
        c = APIClient()
        c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
        r = c.get(ONEROSTER_URL)
        assert r.status_code in (401, 403)

    def test_invalid_school_header_returns_400_or_403(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="staff2@er.com", is_staff=True)
        c = APIClient()
        c.force_authenticate(user=staff)
        # Invalid (non-UUID) header
        c.credentials(HTTP_X_SCHOOL_ID="not-a-uuid")
        r = c.get(ONEROSTER_URL)
        assert r.status_code in (400, 403, 404)


# ---------------------------------------------------------------------------
# Response format
# ---------------------------------------------------------------------------

class TestOneRosterResponseFormat:
    def test_response_is_multipart_mixed(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="fmt@er.com", is_staff=True)
        _seed_academics(school)

        c = _client(staff, school)
        r = c.get(ONEROSTER_URL)
        assert r.status_code == 200
        content_type = r.get("Content-Type", "")
        assert "multipart/mixed" in content_type

    def test_response_contains_orgs_csv(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="orgs@er.com", is_staff=True)

        c = _client(staff, school)
        r = c.get(ONEROSTER_URL)
        assert r.status_code == 200
        body = r.content.decode("utf-8")
        assert "orgs.csv" in body

    def test_response_contains_courses_csv(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="courses@er.com", is_staff=True)
        _seed_academics(school)

        c = _client(staff, school)
        r = c.get(ONEROSTER_URL)
        body = r.content.decode("utf-8")
        assert "courses.csv" in body
        assert "ENG-101" in body

    def test_response_contains_classes_csv(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="classes@er.com", is_staff=True)
        _seed_academics(school)

        c = _client(staff, school)
        r = c.get(ONEROSTER_URL)
        body = r.content.decode("utf-8")
        assert "classes.csv" in body

    def test_response_contains_enrollments_csv(self):
        school = _mk_school()
        staff = _mk_user(school=school, email="enroll@er.com", is_staff=True)
        _seed_academics(school)

        c = _client(staff, school)
        r = c.get(ONEROSTER_URL)
        body = r.content.decode("utf-8")
        assert "enrollments.csv" in body


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

class TestOneRosterTenantIsolation:
    def test_export_only_includes_own_school_courses(self):
        school_a = _mk_school("School A")
        school_b = _mk_school("School B")

        Course.objects.create(school_id=school_a.id, code="MATH-A", name="Math A")
        Course.objects.create(school_id=school_b.id, code="MATH-B", name="Math B")

        staff_a = _mk_user(school=school_a, email="staff_a@iso.com", is_staff=True)
        c = _client(staff_a, school_a)
        r = c.get(ONEROSTER_URL)
        body = r.content.decode("utf-8")

        assert "MATH-A" in body
        assert "MATH-B" not in body, "Cross-school course must NOT appear in export"
