import uuid
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section, TeacherAssignment
from core.models import School, Staff

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE_URL = "/api/v1/section-staffing-wizard/sessions/"


def _school():
    return School.objects.create(name=f"S{uuid.uuid4().hex[:6]}", timezone="America/Chicago", is_active=True)


def _client(school):
    user = User.objects.create_user(
        username=f"u{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _h(school_id):
    return {"HTTP_X_SCHOOL_ID": str(school_id)}


def _canonical_section(school, code="MATH101"):
    course = Course.objects.create(school_id=school.id, code=code, name="Math 101", credits=1)
    return Section.objects.create(school_id=school.id, course=course, term="2026-FALL")


def _teacher(school, email="teacher@example.com", status="ACTIVE"):
    return Staff.objects.create(
        school=school,
        first_name="Test",
        last_name="Teacher",
        email=email,
        role_type="TEACHER",
        status=status,
    )


def _create_configured(client, school):
    response = client.post(BASE_URL, **_h(school.id))
    session_id = response.data["session_id"]
    client.post(
        f"{BASE_URL}{session_id}/configure/",
        {"term": "2026-FALL"},
        format="json",
        **_h(school.id),
    )
    return session_id


class TestSectionStaffingWizardCreate(TestCase):
    def test_create_returns_201(self):
        school = _school()
        client = _client(school)
        response = client.post(BASE_URL, **_h(school.id))
        self.assertEqual(response.status_code, 201)
        self.assertIn("session_id", response.data)

    def test_create_requires_auth(self):
        school = _school()
        response = self.client.post(BASE_URL, HTTP_X_SCHOOL_ID=str(school.id))
        self.assertEqual(response.status_code, 401)


class TestSectionStaffingWizardConfigure(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)
        response = self.client.post(BASE_URL, **_h(self.school.id))
        self.session_id = response.data["session_id"]

    def test_configure_ok(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "configured")
        self.assertEqual(response.data["term"], "2026-FALL")

    def test_verified_session_cannot_be_reconfigured(self):
        section = _canonical_section(self.school)
        teacher = _teacher(self.school)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school.id),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_id": str(section.id)}]},
            format="json",
            **_h(self.school.id),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(section.id), "teacher_id": str(teacher.id), "role": "primary"}]},
            format="json",
            **_h(self.school.id),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.client.get(
            f"{BASE_URL}{self.session_id}/verify/",
            **_h(self.school.id),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2027-SPRING"},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)


class TestSectionStaffingWizardLoadSections(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)
        self.session_id = _create_configured(self.client, self.school)
        self.section = _canonical_section(self.school)
        self.sections_pool = [{"section_id": str(self.section.id), "section_name": "Math 101 A", "course_code": "MATH101", "grade_level": "6"}]

    def test_load_sections_ok(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": self.sections_pool},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["section_count"], 1)

    def test_stage_assignments_wrong_section(self):
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": self.sections_pool},
            format="json",
            **_h(self.school.id),
        )
        bad_assignment = [{"section_id": str(uuid.uuid4()), "teacher_id": str(uuid.uuid4()), "role": "primary"}]
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": bad_assignment},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)

    def test_noncanonical_role_fails_closed(self):
        teacher = _teacher(self.school)
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": self.sections_pool},
            format="json",
            **_h(self.school.id),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(self.section.id), "teacher_id": str(teacher.id), "role": "aide"}]},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)


class TestSectionStaffingWizardCommit(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)
        self.session_id = _create_configured(self.client, self.school)
        self.section = _canonical_section(self.school)
        self.teacher = _teacher(self.school)
        self.sections_pool = [{"section_id": str(self.section.id), "section_name": "Math 101 A", "course_code": "MATH101", "grade_level": "6"}]
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": self.sections_pool},
            format="json",
            **_h(self.school.id),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(self.section.id), "teacher_id": str(self.teacher.id), "role": "primary"}]},
            format="json",
            **_h(self.school.id),
        )

    def test_commit_writes_canonical_teacher_assignment(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["assigned"], 1)
        self.assertTrue(TeacherAssignment.objects.filter(
            school_id=self.school.id,
            section=self.section,
            staff=self.teacher,
        ).exists())

    def test_commit_is_idempotent(self):
        first = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        second = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(TeacherAssignment.objects.filter(section=self.section, staff=self.teacher).count(), 1)

    def test_commit_rejects_cross_tenant_staff(self):
        other_school = _school()
        other_teacher = _teacher(other_school, email="other@example.com")
        from section_staffing_wizard.models import SectionStaffingWizardSession
        session = SectionStaffingWizardSession.objects.get(id=self.session_id)
        session.assignments = [{"section_id": str(self.section.id), "teacher_id": str(other_teacher.id), "role": "primary"}]
        session.save(update_fields=["assignments"])
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TeacherAssignment.objects.filter(section=self.section).exists())

    def test_commit_rejects_cross_tenant_section(self):
        other_school = _school()
        other_section = _canonical_section(other_school, code="SCI101")
        from section_staffing_wizard.models import SectionStaffingWizardSession
        session = SectionStaffingWizardSession.objects.get(id=self.session_id)
        session.assignments = [{"section_id": str(other_section.id), "teacher_id": str(self.teacher.id), "role": "primary"}]
        session.save(update_fields=["assignments"])
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TeacherAssignment.objects.filter(section=other_section).exists())

    def test_commit_rejects_inactive_staff(self):
        inactive = _teacher(self.school, email="inactive@example.com", status="INACTIVE")
        from section_staffing_wizard.models import SectionStaffingWizardSession
        session = SectionStaffingWizardSession.objects.get(id=self.session_id)
        session.assignments = [{"section_id": str(self.section.id), "teacher_id": str(inactive.id), "role": "primary"}]
        session.save(update_fields=["assignments"])
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TeacherAssignment.objects.filter(section=self.section).exists())

    def test_commit_validates_entire_batch_before_writing(self):
        second_section = _canonical_section(self.school, code="ENG101")
        other_school = _school()
        invalid_teacher = _teacher(other_school, email="invalid@example.com")
        from section_staffing_wizard.models import SectionStaffingWizardSession
        session = SectionStaffingWizardSession.objects.get(id=self.session_id)
        session.assignments = [
            {"section_id": str(self.section.id), "teacher_id": str(self.teacher.id), "role": "primary"},
            {"section_id": str(second_section.id), "teacher_id": str(invalid_teacher.id), "role": "primary"},
        ]
        session.save(update_fields=["assignments"])
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school.id),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(TeacherAssignment.objects.filter(school_id=self.school.id).count(), 0)


class TestSectionStaffingWizardTenantIsolation(TestCase):
    def test_cross_tenant_returns_404(self):
        school_a = _school()
        school_b = _school()
        client_a = _client(school_a)
        client_b = _client(school_b)
        response = client_a.post(BASE_URL, **_h(school_a.id))
        session_id = response.data["session_id"]
        response_other = client_b.post(
            f"{BASE_URL}{session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(school_b.id),
        )
        self.assertEqual(response_other.status_code, 404)
