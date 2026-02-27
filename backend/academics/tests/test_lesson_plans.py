"""
Tests for LessonPlan and LessonResource API endpoints.

Covers:
- Tenant scoping: missing/wrong school_id rejected
- Write access: only ADMIN/DIRECTOR roles can create/update
- LessonPlan upsert: POST creates on first call, updates on second
- LessonPlan list: date filter, date_from/date_to range
- LessonPlan detail: GET + PATCH
- Teacher notes visibility: public serializer omits teacher_notes_private
- LessonResource CRUD: create, list, update, delete
- Cross-school isolation: cannot read another school's plans
"""
from __future__ import annotations

import uuid
from datetime import date

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from academics.models import (
    AcademicYear, Course, Enrollment, LessonPlan, LessonResource,
    Lesson, Section, Term, Unit,
)
from core.models import School, UserRole
from households.models import Household, Student

pytestmark = pytest.mark.django_db


User = get_user_model()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mk_school(name="Crowns Academy") -> School:
    return School.objects.create(name=name)


def _mk_user(*, school: School, email: str, is_staff: bool = False) -> User:
    return User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        email=email,
        password="test-pass",
        school=school,
        is_staff=is_staff,
    )


def _assign_role(*, user: User, school: School, role_code: str) -> None:
    UserRole.objects.create(school=school, user=user, role_code=role_code)


def _seed_section(school: School) -> Section:
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
    return Section.objects.create(
        school_id=school.id,
        course=course,
        term_ref=term,
        term="2026-FALL",
    )


def _seed_lesson(school: School, section: Section) -> Lesson:
    """Create a minimal Lesson attached to the section's first unit."""
    unit = Unit.objects.create(
        school_id=school.id,
        course=section.course,
        title="Unit 1",
        sequence_order=1,
    )
    return Lesson.objects.create(
        school_id=school.id,
        unit=unit,
        title="Day 1 Lesson",
    )


def _client_auth(user: User, school: School) -> APIClient:
    c = APIClient()
    c.force_authenticate(user=user)
    c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
    return c


# ---------------------------------------------------------------------------
# LessonPlan Tenant Scoping
# ---------------------------------------------------------------------------

class TestLessonPlanTenantScoping:
    """Verify that the endpoint is scoped to X-School-Id."""

    def test_invalid_school_header_uuid_returns_400(self):
        """An unparseable UUID in X-School-Id must be rejected with 400."""
        school = _mk_school()
        user = _mk_user(school=school, email="admin@test.com")
        _assign_role(user=user, school=school, role_code="ADMIN")

        section = _seed_section(school)

        c = APIClient()
        c.force_authenticate(user=user)
        c.credentials(HTTP_X_SCHOOL_ID="not-a-valid-uuid")
        r = c.get(f"/api/academics/sections/{section.id}/lesson-plans/")
        assert r.status_code in (400, 403, 404), f"Expected 400/403/404, got {r.status_code}"

    def test_valid_school_header_lists_empty_plans(self):
        school = _mk_school("Crown B")
        user = _mk_user(school=school, email="admin2@test.com")
        _assign_role(user=user, school=school, role_code="ADMIN")

        section = _seed_section(school)
        c = _client_auth(user, school)
        r = c.get(f"/api/academics/sections/{section.id}/lesson-plans/")
        assert r.status_code == 200
        assert r.data == []

    def test_cross_school_section_returns_404(self):
        school_a = _mk_school("Crown A")
        school_b = _mk_school("Crown B")

        user_a = _mk_user(school=school_a, email="a@a.com")
        _assign_role(user=user_a, school=school_a, role_code="ADMIN")

        section_b = _seed_section(school_b)

        c = _client_auth(user_a, school_a)
        # Section belongs to school_b, but header is school_a → 404
        r = c.get(f"/api/academics/sections/{section_b.id}/lesson-plans/")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# LessonPlan Create (POST upsert)
# ---------------------------------------------------------------------------

class TestLessonPlanCreate:
    """POST upsert: create on first call, update on second."""

    def test_admin_can_create_lesson_plan(self):
        school = _mk_school()
        user = _mk_user(school=school, email="admin@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        c = _client_auth(user, school)
        r = c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-09-01",
            "objectives": "Understand subject-verb agreement.",
            "materials": "Textbook ch.1",
            "activities": "Group discussion",
            "homework": "p.14 exercises",
            "teacher_notes_private": "Watch for struggling students.",
        }, format="json")

        assert r.status_code == 201, r.data
        assert r.data["plan_date"] == "2026-09-01"
        assert r.data["objectives"] == "Understand subject-verb agreement."
        assert r.data["teacher_notes_private"] == "Watch for struggling students."
        assert str(r.data["section_id"]) == str(section.id)

    def test_post_again_same_date_updates_and_returns_200(self):
        school = _mk_school()
        user = _mk_user(school=school, email="admin2@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        c = _client_auth(user, school)
        c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-09-02",
            "objectives": "Original",
        }, format="json")

        r2 = c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-09-02",
            "objectives": "Updated objectives",
        }, format="json")

        assert r2.status_code == 200
        assert r2.data["objectives"] == "Updated objectives"
        # DB should have only one plan for this date
        assert LessonPlan.objects.filter(section=section, plan_date="2026-09-02").count() == 1

    def test_missing_plan_date_returns_400(self):
        school = _mk_school()
        user = _mk_user(school=school, email="nodate@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        c = _client_auth(user, school)
        r = c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "objectives": "No date here",
        }, format="json")

        assert r.status_code == 400

    def test_non_admin_cannot_create_lesson_plan(self):
        school = _mk_school()
        viewer = _mk_user(school=school, email="viewer@school.com")
        section = _seed_section(school)

        c = _client_auth(viewer, school)
        r = c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-09-03",
            "objectives": "Unauthorized attempt",
        }, format="json")

        assert r.status_code == 403

    def test_unauthenticated_returns_401_or_403(self):
        school = _mk_school()
        section = _seed_section(school)

        c = APIClient()
        c.credentials(HTTP_X_SCHOOL_ID=str(school.id))
        r = c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-09-04",
            "objectives": "Unauth attempt",
        }, format="json")

        assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# LessonPlan List + Filtering
# ---------------------------------------------------------------------------

class TestLessonPlanList:
    """GET list with date filters."""

    def _create_plans(self, school, section, user):
        c = _client_auth(user, school)
        dates = ["2026-09-01", "2026-09-02", "2026-09-03"]
        for d in dates:
            c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
                "plan_date": d,
                "objectives": f"Plan for {d}",
            }, format="json")
        return dates

    def test_list_all_plans(self):
        school = _mk_school()
        user = _mk_user(school=school, email="list@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        dates = self._create_plans(school, section, user)
        c = _client_auth(user, school)
        r = c.get(f"/api/academics/sections/{section.id}/lesson-plans/")
        assert r.status_code == 200
        assert len(r.data) == 3

    def test_filter_by_single_date(self):
        school = _mk_school()
        user = _mk_user(school=school, email="filter@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        self._create_plans(school, section, user)
        c = _client_auth(user, school)
        r = c.get(f"/api/academics/sections/{section.id}/lesson-plans/?date=2026-09-02")
        assert r.status_code == 200
        assert len(r.data) == 1
        assert r.data[0]["plan_date"] == "2026-09-02"

    def test_filter_by_date_range(self):
        school = _mk_school()
        user = _mk_user(school=school, email="range@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        self._create_plans(school, section, user)
        c = _client_auth(user, school)
        r = c.get(
            f"/api/academics/sections/{section.id}/lesson-plans/"
            "?date_from=2026-09-01&date_to=2026-09-02"
        )
        assert r.status_code == 200
        assert len(r.data) == 2


# ---------------------------------------------------------------------------
# Teacher Notes Privacy
# ---------------------------------------------------------------------------

class TestTeacherNotesPrivacy:
    """Public serializer omits teacher_notes_private for non-role users."""

    def test_admin_sees_teacher_notes(self):
        school = _mk_school()
        admin = _mk_user(school=school, email="admin_priv@school.com")
        _assign_role(user=admin, school=school, role_code="ADMIN")
        section = _seed_section(school)

        c = _client_auth(admin, school)
        c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-10-01",
            "teacher_notes_private": "Private teacher note.",
        }, format="json")

        r = c.get(f"/api/academics/sections/{section.id}/lesson-plans/")
        assert r.status_code == 200
        assert r.data[0]["teacher_notes_private"] == "Private teacher note."

    def test_unauthenticated_user_does_not_see_teacher_notes(self):
        """Non-role user gets the public serializer (no teacher_notes_private field)."""
        school = _mk_school()
        admin = _mk_user(school=school, email="admin_pub@school.com")
        _assign_role(user=admin, school=school, role_code="ADMIN")
        section = _seed_section(school)

        c_admin = _client_auth(admin, school)
        c_admin.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": "2026-10-05",
            "teacher_notes_private": "Top secret.",
        }, format="json")

        # Regular user with no role
        plain_user = _mk_user(school=school, email="plain@school.com")
        c_plain = _client_auth(plain_user, school)
        r = c_plain.get(f"/api/academics/sections/{section.id}/lesson-plans/")
        assert r.status_code == 200
        # Public serializer does not include teacher_notes_private
        assert "teacher_notes_private" not in r.data[0]


# ---------------------------------------------------------------------------
# LessonPlan Detail (GET + PATCH)
# ---------------------------------------------------------------------------

class TestLessonPlanDetail:
    """Individual plan retrieval and update."""

    def _create_plan(self, school, section, user, plan_date="2026-11-01") -> str:
        c = _client_auth(user, school)
        r = c.post(f"/api/academics/sections/{section.id}/lesson-plans/", {
            "plan_date": plan_date,
            "objectives": "Initial objective",
        }, format="json")
        return str(r.data["plan_id"])

    def test_get_plan_by_id(self):
        school = _mk_school()
        user = _mk_user(school=school, email="detail@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        plan_id = self._create_plan(school, section, user)
        c = _client_auth(user, school)
        r = c.get(f"/api/academics/lesson-plans/{plan_id}/")
        assert r.status_code == 200
        assert r.data["plan_id"] == plan_id

    def test_patch_updates_objectives(self):
        school = _mk_school()
        user = _mk_user(school=school, email="patch@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)

        plan_id = self._create_plan(school, section, user)
        c = _client_auth(user, school)
        r = c.patch(f"/api/academics/lesson-plans/{plan_id}/", {
            "objectives": "Updated objectives via PATCH",
        }, format="json")
        assert r.status_code == 200
        assert r.data["objectives"] == "Updated objectives via PATCH"

    def test_cross_school_plan_returns_404(self):
        school_a = _mk_school("A School")
        school_b = _mk_school("B School")
        user_a = _mk_user(school=school_a, email="a@cross.com")
        user_b = _mk_user(school=school_b, email="b@cross.com")
        _assign_role(user=user_a, school=school_a, role_code="ADMIN")
        _assign_role(user=user_b, school=school_b, role_code="ADMIN")

        section_b = _seed_section(school_b)
        plan_id = self._create_plan(school_b, section_b, user_b)

        # user_a cannot access school_b's plan
        c_a = _client_auth(user_a, school_a)
        r = c_a.get(f"/api/academics/lesson-plans/{plan_id}/")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# LessonResource CRUD
# ---------------------------------------------------------------------------

class TestLessonResourceCRUD:
    """Create, list, update, delete lesson resources."""

    def _setup(self):
        school = _mk_school()
        user = _mk_user(school=school, email="res@school.com")
        _assign_role(user=user, school=school, role_code="ADMIN")
        section = _seed_section(school)
        lesson = _seed_lesson(school, section)
        return school, user, section, lesson

    def test_create_resource(self):
        school, user, section, lesson = self._setup()
        c = _client_auth(user, school)
        r = c.post(f"/api/academics/lessons/{lesson.id}/resources/", {
            "title": "BJU Press Chapter 1 PDF",
            "kind": "link",
            "url": "https://example.com/chapter1.pdf",
        }, format="json")
        assert r.status_code == 201
        assert r.data["title"] == "BJU Press Chapter 1 PDF"
        assert r.data["kind"] == "link"

    def test_list_resources_for_lesson(self):
        school, user, section, lesson = self._setup()
        LessonResource.objects.create(
            school_id=school.id,
            lesson=lesson,
            title="Resource A",
            kind="video",
            url="https://example.com/video",
        )
        LessonResource.objects.create(
            school_id=school.id,
            lesson=lesson,
            title="Resource B",
            kind="doc",
            url="https://example.com/doc",
        )
        c = _client_auth(user, school)
        r = c.get(f"/api/academics/lessons/{lesson.id}/resources/")
        assert r.status_code == 200
        assert len(r.data) == 2

    def test_create_resource_missing_title_returns_400(self):
        school, user, section, lesson = self._setup()
        c = _client_auth(user, school)
        r = c.post(f"/api/academics/lessons/{lesson.id}/resources/", {
            "kind": "link",
            "url": "https://example.com",
        }, format="json")
        assert r.status_code == 400

    def test_non_admin_cannot_create_resource(self):
        school = _mk_school()
        section = _seed_section(school)
        lesson = _seed_lesson(school, section)
        viewer = _mk_user(school=school, email="viewer_res@school.com")

        c = _client_auth(viewer, school)
        r = c.post(f"/api/academics/lessons/{lesson.id}/resources/", {
            "title": "Unauthorized resource",
        }, format="json")
        assert r.status_code == 403

    def test_patch_resource(self):
        school, user, section, lesson = self._setup()
        res = LessonResource.objects.create(
            school_id=school.id,
            lesson=lesson,
            title="Old Title",
            kind="link",
            url="https://old.com",
        )
        c = _client_auth(user, school)
        r = c.patch(f"/api/academics/lesson-resources/{res.id}/", {
            "title": "New Title",
            "url": "https://new.com",
        }, format="json")
        assert r.status_code == 200
        assert r.data["title"] == "New Title"

    def test_delete_resource(self):
        school, user, section, lesson = self._setup()
        res = LessonResource.objects.create(
            school_id=school.id,
            lesson=lesson,
            title="To Delete",
            kind="doc",
        )
        c = _client_auth(user, school)
        r = c.delete(f"/api/academics/lesson-resources/{res.id}/")
        assert r.status_code == 204
        assert not LessonResource.objects.filter(id=res.id).exists()

    def test_cross_school_resource_returns_404(self):
        school_a = _mk_school()
        school_b = _mk_school()
        user_a = _mk_user(school=school_a, email="xa@school.com")
        user_b = _mk_user(school=school_b, email="xb@school.com")
        _assign_role(user=user_a, school=school_a, role_code="ADMIN")
        _assign_role(user=user_b, school=school_b, role_code="ADMIN")

        section_b = _seed_section(school_b)
        lesson_b = _seed_lesson(school_b, section_b)
        res = LessonResource.objects.create(
            school_id=school_b.id,
            lesson=lesson_b,
            title="B Resource",
        )
        c_a = _client_auth(user_a, school_a)
        r = c_a.get(f"/api/academics/lesson-resources/{res.id}/")
        assert r.status_code == 404
