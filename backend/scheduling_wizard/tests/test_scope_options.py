from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Term
from core.models import AcademicYear, CrownPermission, RolePermission, School, UserRole


User = get_user_model()


class SchedulingScopeOptionsTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Scope School", timezone="America/New_York", is_active=True)
        self.other_school = School.objects.create(name="Other Scope School", timezone="America/New_York", is_active=True)
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
            code="S1",
            name="Semester 1",
            school_year=self.year.name,
            start_date=date(2026, 8, 20),
            end_date=date(2027, 1, 15),
            ordering=1,
            active=True,
        )
        other_year = AcademicYear.objects.create(
            school=self.other_school,
            name="2026-2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 30),
            is_current=True,
        )
        Term.objects.create(
            school_id=self.other_school.id,
            academic_year=other_year,
            code="S1",
            name="Other Semester",
            school_year=other_year.name,
            ordering=1,
            active=True,
        )
        user = User.objects.create_user(username="scope-user", password="test-only", school=self.school)
        UserRole.objects.create(user=user, school=self.school, role_code="SCOPE_TEST")
        permission, _ = CrownPermission.objects.get_or_create(
            code="scheduling.view",
            defaults={"description": "View scheduling"},
        )
        RolePermission.objects.create(role_code="SCOPE_TEST", permission=permission)
        self.client = APIClient()
        self.client.force_authenticate(user=user)

    def test_scope_options_are_canonical_and_tenant_scoped(self):
        response = self.client.get(
            "/api/v1/scheduling-wizard/sessions/scope-options/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [row["academic_year_id"] for row in response.data["academic_years"]],
            [str(self.year.id)],
        )
        self.assertEqual(
            [row["term_id"] for row in response.data["terms"]],
            [str(self.term.id)],
        )
        self.assertEqual(response.data["terms"][0]["academic_year_id"], str(self.year.id))
