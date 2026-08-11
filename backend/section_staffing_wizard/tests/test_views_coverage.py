import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section, TeacherAssignment
from core.models import School, Staff
from section_staffing_wizard.models import SectionStaffingWizardSession

TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"
User = get_user_model()
BASE_URL = "/api/v1/section-staffing-wizard/sessions/"


def _school():
    return School.objects.create(
        name=f"S{uuid.uuid4().hex[:6]}",
        timezone="America/Chicago",
        is_active=True,
    )


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


def _h(school):
    return {"HTTP_X_SCHOOL_ID": str(school.id)}


def _session(client, school):
    response = client.post(BASE_URL, **_h(school))
    return response.data["session_id"]


def _section(school, code="MATH101"):
    course = Course.objects.create(
        school_id=school.id,
        code=code,
        name=code,
        credits=1,
    )
    return Section.objects.create(
        school_id=school.id,
        course=course,
        term="2026-FALL",
    )


def _staff(school, email="teacher@example.com"):
    return Staff.objects.create(
        school=school,
        first_name="Test",
        last_name="Teacher",
        email=email,
        role_type="TEACHER",
        status="ACTIVE",
    )


class TestSectionStaffingWizardCoverageBranches(TestCase):
    def setUp(self):
        self.school = _school()
        self.client = _client(self.school)
        self.session_id = _session(self.client, self.school)

    def test_configure_rejects_invalid_academic_year_uuid(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"academic_year_id": "not-a-uuid", "term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("valid UUID", response.data["error"])

    def test_configure_accepts_academic_year_uuid(self):
        academic_year_id = uuid.uuid4()
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"academic_year_id": str(academic_year_id), "term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["academic_year_id"], str(academic_year_id))

    def test_load_sections_requires_configured_state(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_id": str(uuid.uuid4())}]},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_load_sections_rejects_empty_pool(self):
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": []},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_load_sections_rejects_missing_section_id(self):
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_name": "Missing ID"}]},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_stage_assignments_requires_loaded_state(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(uuid.uuid4()), "teacher_id": str(uuid.uuid4())}]},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_stage_assignments_rejects_empty_assignments(self):
        section = _section(self.school)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_id": str(section.id)}]},
            format="json",
            **_h(self.school),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": []},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_stage_assignments_rejects_missing_teacher(self):
        section = _section(self.school)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_id": str(section.id)}]},
            format="json",
            **_h(self.school),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(section.id), "role": "primary"}]},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_commit_requires_staged_state(self):
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_commit_requires_confirmation(self):
        section = _section(self.school)
        staff = _staff(self.school)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_id": str(section.id)}]},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(section.id), "teacher_id": str(staff.id), "role": "primary"}]},
            format="json",
            **_h(self.school),
        )
        response = self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {},
            format="json",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(TeacherAssignment.objects.filter(section=section, staff=staff).exists())

    def test_verify_requires_committed_state(self):
        response = self.client.get(
            f"{BASE_URL}{self.session_id}/verify/",
            **_h(self.school),
        )
        self.assertEqual(response.status_code, 400)

    def test_verify_promotes_committed_session_and_is_repeatable(self):
        section = _section(self.school)
        staff = _staff(self.school)
        self.client.post(
            f"{BASE_URL}{self.session_id}/configure/",
            {"term": "2026-FALL"},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/load_sections/",
            {"sections_pool": [{"section_id": str(section.id)}]},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/stage_assignments/",
            {"assignments": [{"section_id": str(section.id), "teacher_id": str(staff.id), "role": "primary"}]},
            format="json",
            **_h(self.school),
        )
        self.client.post(
            f"{BASE_URL}{self.session_id}/commit/",
            {"confirm": True},
            format="json",
            **_h(self.school),
        )
        first = self.client.get(f"{BASE_URL}{self.session_id}/verify/", **_h(self.school))
        second = self.client.get(f"{BASE_URL}{self.session_id}/verify/", **_h(self.school))
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.data["status"], SectionStaffingWizardSession.STATUS_VERIFIED)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.data["status"], SectionStaffingWizardSession.STATUS_VERIFIED)
