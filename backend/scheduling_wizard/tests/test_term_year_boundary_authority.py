from datetime import date
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Term
from core.models import AcademicYear, CrownPermission, RolePermission, School, UserRole


BASE_URL = "/api/v1/scheduling-wizard/sessions/"
ROLE_CODE = "SCHEDULING_TERM_BOUNDARY_TEST"
PERMISSIONS = (
    "scheduling.view",
    "scheduling.configure",
    "scheduling.edit",
    "scheduling.publish",
)
User = get_user_model()


class SchedulingTermYearBoundaryAuthorityTest(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            name="Scheduling Boundary School",
            timezone="America/Chicago",
            is_active=True,
        )
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 30),
            is_current=True,
        )
        self.term = Term.objects.create(
            school_id=self.school.id,
            academic_year=self.year,
            code="2026-FALL",
            name="Fall 2026",
            school_year=self.year.name,
            start_date=date(2026, 8, 1),
            end_date=date(2026, 12, 31),
            ordering=1,
            active=True,
        )
        user = User.objects.create_user(
            username=f"scheduler-{uuid.uuid4().hex[:8]}",
            school=self.school,
        )
        UserRole.objects.create(user=user, school=self.school, role_code=ROLE_CODE)
        for code in PERMISSIONS:
            permission, _ = CrownPermission.objects.get_or_create(
                code=code,
                defaults={"description": f"Test permission {code}"},
            )
            RolePermission.objects.get_or_create(role_code=ROLE_CODE, permission=permission)
        self.client = APIClient()
        self.client.force_authenticate(user=user)
        self.headers = {"HTTP_X_SCHOOL_ID": str(self.school.id)}

    def _create_session(self):
        response = self.client.post(BASE_URL, **self.headers)
        self.assertEqual(response.status_code, 201)
        return response.data["session_id"]

    def _configure(self, session_id):
        return self.client.post(
            f"{BASE_URL}{session_id}/configure/",
            {
                "academic_year_id": str(self.year.id),
                "term_id": str(self.term.id),
            },
            format="json",
            **self.headers,
        )

    def test_configure_rejects_term_dates_outside_academic_year(self):
        self.term.start_date = date(2027, 8, 1)
        self.term.end_date = date(2027, 12, 31)
        self.term.save(update_fields=["start_date", "end_date", "updated_at"])
        session_id = self._create_session()

        response = self._configure(session_id)

        self.assertEqual(response.status_code, 400)
        self.assertIn("outside", response.data["error"])

    def test_commit_revalidates_term_boundary_after_configuration(self):
        session_id = self._create_session()
        self.assertEqual(self._configure(session_id).status_code, 200)
        courses = self.client.post(
            f"{BASE_URL}{session_id}/courses/",
            {"courses": [{"code": "MATH101", "name": "Algebra I", "credits": "1.0"}]},
            format="json",
            **self.headers,
        )
        self.assertEqual(courses.status_code, 200)
        sections = self.client.post(
            f"{BASE_URL}{session_id}/sections/",
            {"sections": [{"course_code": "MATH101"}]},
            format="json",
            **self.headers,
        )
        self.assertEqual(sections.status_code, 200)

        self.term.start_date = date(2027, 8, 1)
        self.term.end_date = date(2027, 12, 31)
        self.term.save(update_fields=["start_date", "end_date", "updated_at"])

        response = self.client.post(
            f"{BASE_URL}{session_id}/commit/",
            {"confirm": True},
            format="json",
            **self.headers,
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("outside", response.data["error"])
