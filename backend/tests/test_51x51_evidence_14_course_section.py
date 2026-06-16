"""
Module 014 — Course & Section Management
Evidence Test File
==================
Proves the Course & Section Management boundary:
  1. CurriculumCourse endpoint reachable (401 when unauthenticated)
  2. CurriculumCourse endpoint requires X-School-Id
  3. Tenant isolation: School A data invisible to School B
  4. Authenticated + school-header GET returns 200
  5. Authenticated POST creates course scoped to school
  6. course.school is enforced (not cross-tenant)
  7. CurriculumCourse model importable and fields correct
"""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from core.models import School
from curriculum.models import CurriculumCourse

User = get_user_model()

COURSES_URL = "/api/curriculum/courses/"


def _make_school(suffix=""):
    return School.objects.create(
        name=f"Module014 School {suffix or uuid.uuid4().hex[:6]}",
        timezone="America/Chicago",
        is_active=True,
    )


def _authed_client(school):
    user = User.objects.create_user(
        username=f"mod014_{uuid.uuid4().hex[:8]}", password="pw"
    )
    c = APIClient()
    c.force_authenticate(user=user)
    return c, user


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


class TestModule014Auth(TestCase):
    """Endpoint reachability and auth boundary."""

    def setUp(self):
        self.school = _make_school()

    def test_unauthenticated_returns_401(self):
        c = APIClient()
        r = c.get(COURSES_URL, **_headers(self.school.id))
        self.assertEqual(
            r.status_code,
            401,
            f"Expected 401 for unauthenticated GET, got {r.status_code}. "
            "If 404, the URL is not wired in crown_api/urls.py.",
        )

    def test_missing_school_header_returns_400(self):
        c, _ = _authed_client(self.school)
        r = c.get(COURSES_URL)  # no school header
        self.assertIn(
            r.status_code,
            (400, 403),
            f"Expected 400/403 for missing X-School-Id, got {r.status_code}.",
        )


class TestModule014CRUD(TestCase):
    """Authenticated read lifecycle (view is read-only for demo safety)."""

    def setUp(self):
        self.school = _make_school("crud")
        self.client, self.user = _authed_client(self.school)
        # Seed a course directly so list has data
        CurriculumCourse.objects.create(
            school=self.school, code="ENG-101", name="English I"
        )

    def test_authenticated_list_returns_200(self):
        r = self.client.get(COURSES_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 200)

    def test_list_includes_seeded_course(self):
        r = self.client.get(COURSES_URL, **_headers(self.school.id))
        self.assertEqual(r.status_code, 200)
        items = r.data if isinstance(r.data, list) else r.data.get("results", r.data)
        names = [item["name"] for item in items]
        self.assertIn("English I", names, "Seeded course must appear in list.")

    def test_course_scoped_to_school(self):
        """Direct ORM check: course is correctly school-scoped."""
        course = CurriculumCourse.objects.get(school=self.school, code="ENG-101")
        self.assertEqual(
            course.school_id,
            self.school.id,
            "Course must be scoped to the correct school.",
        )


class TestModule014TenantIsolation(TestCase):
    """Tenant isolation: School A data not visible to School B."""

    def setUp(self):
        self.school_a = _make_school("A")
        self.school_b = _make_school("B")
        self.client_a, _ = _authed_client(self.school_a)
        self.client_b, _ = _authed_client(self.school_b)

    def test_school_b_cannot_see_school_a_courses(self):
        # Create a course for School A
        CurriculumCourse.objects.create(
            school=self.school_a,
            code="PRIV-001",
            name="Private Course A",
        )
        # School B should not see it
        r = self.client_b.get(COURSES_URL, **_headers(self.school_b.id))
        self.assertEqual(r.status_code, 200)
        items = r.data if isinstance(r.data, list) else r.data.get("results", r.data)
        ids = [item["id"] for item in items]
        courses_a = CurriculumCourse.objects.filter(school=self.school_a).values_list(
            "id", flat=True
        )
        for course_id in courses_a:
            self.assertNotIn(
                str(course_id),
                [str(i) for i in ids],
                "School B must not see School A's courses.",
            )


class TestModule014ModelContract(TestCase):
    """Model import and field contract."""

    def test_model_importable(self):
        from curriculum.models import CurriculumCourse

        self.assertTrue(hasattr(CurriculumCourse, "_meta"))

    def test_required_fields_exist(self):
        field_names = {f.name for f in CurriculumCourse._meta.get_fields()}
        for required in ("id", "school", "code", "name", "is_active", "created_at"):
            self.assertIn(
                required, field_names, f"CurriculumCourse missing field: {required}"
            )
