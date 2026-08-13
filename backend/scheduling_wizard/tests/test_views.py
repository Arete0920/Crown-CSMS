import uuid
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section, Term
from core.models import (
    AcademicYear,
    CrownPermission,
    RolePermission,
    School,
    UserRole,
)
from scheduling_wizard.models import SchedulingWizardSession


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
ROLE_CODE = "SCHEDULING_TEST_ADMIN"
PERMISSIONS = (
    "scheduling.view",
    "scheduling.configure",
    "scheduling.edit",
    "scheduling.publish",
)

User = get_user_model()
BASE_URL = "/api/v1/scheduling-wizard/sessions/"

VALID_COURSES = [
    {"code": "MATH101", "name": "Algebra I", "department": "Mathematics", "credits": "1.0"},
    {"code": "ENG101", "name": "English Composition", "department": "English", "credits": "1.0"},
]


def _make_school(name="Scheduling School"):
    return School.objects.create(name=name, timezone="America/Chicago", is_active=True)


def _make_academic_year_and_term(school, name="2026-2027", code="2026-FALL"):
    academic_year = AcademicYear.objects.create(
        school=school,
        name=name,
        start_date=date(2026, 8, 1),
        end_date=date(2027, 6, 30),
        is_current=True,
    )
    term = Term.objects.create(
        school_id=school.id,
        academic_year=academic_year,
        code=code,
        name="Fall 2026",
        school_year=name,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 12, 31),
        ordering=1,
        active=True,
    )
    return academic_year, term


def _grant_scheduling_role(user, school):
    UserRole.objects.create(user=user, school=school, role_code=ROLE_CODE)
    for code in PERMISSIONS:
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,
            defaults={"description": f"Test permission {code}"},
        )
        RolePermission.objects.get_or_create(role_code=ROLE_CODE, permission=permission)


def _make_user(school, username=None, grant_permissions=True):
    username = username or f"user_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=username, password=TEST_AUTH_SECRET, school=school)
    if grant_permissions:
        _grant_scheduling_role(user, school)
    return user


def _headers(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _client_for(school, grant_permissions=True):
    user = _make_user(school, grant_permissions=grant_permissions)
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class SchedulingWizardCase(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.academic_year, self.term = _make_academic_year_and_term(self.school)
        self.client = _client_for(self.school)

    def create_session(self):
        response = self.client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(response.status_code, 201)
        return response.data["session_id"]

    def configure(self, session_id, academic_year=None, term=None):
        academic_year = academic_year or self.academic_year
        term = term or self.term
        return self.client.post(
            f"{BASE_URL}{session_id}/configure/",
            {"academic_year_id": str(academic_year.id), "term_id": str(term.id)},
            format="json",
            **_headers(self.school.id),
        )

    def save_courses(self, session_id, courses=None):
        return self.client.post(
            f"{BASE_URL}{session_id}/courses/",
            {"courses": courses or VALID_COURSES},
            format="json",
            **_headers(self.school.id),
        )

    def stage_sections(self, session_id, sections):
        return self.client.post(
            f"{BASE_URL}{session_id}/sections/",
            {"sections": sections},
            format="json",
            **_headers(self.school.id),
        )

    def prepare(self, sections):
        session_id = self.create_session()
        self.assertEqual(self.configure(session_id).status_code, 200)
        self.assertEqual(self.save_courses(session_id).status_code, 200)
        staged = self.stage_sections(session_id, sections)
        self.assertEqual(staged.status_code, 200)
        return session_id, staged

    def commit(self, session_id, confirm=True):
        return self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": confirm},
            format="json",
            **_headers(self.school.id),
        )


class TestAuthAndPermissions(TestCase):
    def setUp(self):
        self.school = _make_school()
        self.academic_year, self.term = _make_academic_year_and_term(self.school)

    def test_create_requires_auth(self):
        response = APIClient().post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(response.status_code, 401)

    def test_create_requires_scheduling_permission(self):
        client = _client_for(self.school, grant_permissions=False)
        response = client.post(BASE_URL, **_headers(self.school.id))
        self.assertEqual(response.status_code, 403)


class TestTenantIsolation(TestCase):
    def setUp(self):
        self.school_a = _make_school("School A")
        self.school_b = _make_school("School B")
        self.year_a, self.term_a = _make_academic_year_and_term(self.school_a)
        self.year_b, self.term_b = _make_academic_year_and_term(self.school_b)
        self.client_a = _client_for(self.school_a)
        self.client_b = _client_for(self.school_b)
        response = self.client_a.post(BASE_URL, **_headers(self.school_a.id))
        self.session_id = response.data["session_id"]

    def test_other_school_cannot_configure_session(self):
        response = self.client_b.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"academic_year_id": str(self.year_b.id), "term_id": str(self.term_b.id)},
            format="json",
            **_headers(self.school_b.id),
        )
        self.assertEqual(response.status_code, 404)

    def test_configure_rejects_cross_tenant_term(self):
        response = self.client_a.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"academic_year_id": str(self.year_a.id), "term_id": str(self.term_b.id)},
            format="json",
            **_headers(self.school_a.id),
        )
        self.assertEqual(response.status_code, 404)


class TestConfigure(SchedulingWizardCase):
    def test_configure_uses_canonical_year_and_term(self):
        session_id = self.create_session()
        response = self.configure(session_id)
        self.assertEqual(response.status_code, 200)
        session = SchedulingWizardSession.objects.get(id=session_id)
        self.assertEqual(session.academic_year_id, self.academic_year.id)
        self.assertEqual(session.term_ref_id, self.term.id)
        self.assertEqual(session.term, self.term.code)

    def test_configure_requires_canonical_ids(self):
        session_id = self.create_session()
        response = self.client.post(
            f"{BASE_URL}{session_id}/configure/",
            {"term": "2026-FALL", "school_year": "2026-2027"},
            format="json",
            **_headers(self.school.id),
        )
        self.assertEqual(response.status_code, 400)

    def test_configure_rejects_term_from_different_year(self):
        other_year = AcademicYear.objects.create(
            school=self.school,
            name="2027-2028",
            start_date=date(2027, 8, 1),
            end_date=date(2028, 6, 30),
            is_current=False,
        )
        session_id = self.create_session()
        response = self.configure(session_id, academic_year=other_year, term=self.term)
        self.assertEqual(response.status_code, 400)


class TestCourseAndSectionStaging(SchedulingWizardCase):
    def test_duplicate_course_code_rejected(self):
        session_id = self.create_session()
        self.assertEqual(self.configure(session_id).status_code, 200)
        response = self.save_courses(
            session_id,
            [
                {"code": "MATH101", "name": "Algebra"},
                {"code": "MATH101", "name": "Algebra II"},
            ],
        )
        self.assertEqual(response.status_code, 400)

    def test_parallel_sections_get_distinct_canonical_ids(self):
        session_id = self.create_session()
        self.assertEqual(self.configure(session_id).status_code, 200)
        self.assertEqual(self.save_courses(session_id).status_code, 200)
        response = self.stage_sections(
            session_id,
            [
                {"course_code": "MATH101", "teacher_name": "Teacher A"},
                {"course_code": "MATH101", "teacher_name": "Teacher B"},
            ],
        )
        self.assertEqual(response.status_code, 200)
        ids = [item["section_id"] for item in response.data["sections"]]
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)

    def test_supplied_duplicate_section_id_rejected(self):
        session_id = self.create_session()
        self.assertEqual(self.configure(session_id).status_code, 200)
        self.assertEqual(self.save_courses(session_id).status_code, 200)
        section_id = str(uuid.uuid4())
        response = self.stage_sections(
            session_id,
            [
                {"section_id": section_id, "course_code": "MATH101"},
                {"section_id": section_id, "course_code": "ENG101"},
            ],
        )
        self.assertEqual(response.status_code, 400)


class TestCanonicalCommit(SchedulingWizardCase):
    def test_two_sections_same_course_term_persist_independently(self):
        session_id, staged = self.prepare(
            [
                {"course_code": "MATH101", "teacher_name": "Teacher A"},
                {"course_code": "MATH101", "teacher_name": "Teacher B"},
            ]
        )
        expected_ids = {item["section_id"] for item in staged.data["sections"]}
        response = self.commit(session_id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["sections_created"], 2)

        sections = Section.objects.filter(
            school_id=self.school.id,
            course__code="MATH101",
            term_ref=self.term,
        )
        self.assertEqual(sections.count(), 2)
        self.assertEqual({str(section.id) for section in sections}, expected_ids)
        self.assertTrue(all(section.term == self.term.code for section in sections))

    def test_commit_is_idempotent(self):
        session_id, _ = self.prepare(
            [{"course_code": "MATH101"}, {"course_code": "MATH101"}]
        )
        first = self.commit(session_id)
        second = self.commit(session_id)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            Section.objects.filter(school_id=self.school.id, course__code="MATH101", term_ref=self.term).count(),
            2,
        )

    def test_commit_requires_explicit_confirmation(self):
        session_id, _ = self.prepare([{"course_code": "MATH101"}])
        response = self.commit(session_id, confirm=False)
        self.assertEqual(response.status_code, 400)

    def test_existing_section_id_with_different_identity_returns_conflict(self):
        session_id = self.create_session()
        self.assertEqual(self.configure(session_id).status_code, 200)
        self.assertEqual(self.save_courses(session_id).status_code, 200)

        other_school = _make_school("Other School")
        other_year, other_term = _make_academic_year_and_term(other_school)
        other_course = Course.objects.create(school_id=other_school.id, code="MATH101", name="Other Algebra")
        conflicting_id = uuid.uuid4()
        Section.objects.create(
            id=conflicting_id,
            school_id=other_school.id,
            course=other_course,
            term_ref=other_term,
            term=other_term.code,
        )
        staged = self.stage_sections(
            session_id,
            [{"section_id": str(conflicting_id), "course_code": "MATH101"}],
        )
        self.assertEqual(staged.status_code, 200)
        response = self.commit(session_id)
        self.assertEqual(response.status_code, 409)


class TestVerify(SchedulingWizardCase):
    def test_verify_checks_persisted_canonical_sections(self):
        session_id, _ = self.prepare([{"course_code": "MATH101"}])
        self.assertEqual(self.commit(session_id).status_code, 200)
        response = self.client.get(
            f"{BASE_URL}{session_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "verified")

    def test_verify_fails_if_committed_section_is_missing(self):
        session_id, staged = self.prepare([{"course_code": "MATH101"}])
        self.assertEqual(self.commit(session_id).status_code, 200)
        Section.objects.filter(id=staged.data["sections"][0]["section_id"]).delete()
        response = self.client.get(
            f"{BASE_URL}{session_id}/verify/",
            **_headers(self.school.id),
        )
        self.assertEqual(response.status_code, 409)
        self.assertIn("missing_section_ids", response.data)
