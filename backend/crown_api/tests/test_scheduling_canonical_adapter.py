from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, Term
from core.models import AcademicYear, School, UserAccount
from households.models import Guardian, Household, Student


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


class CanonicalSchedulingAdapterTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Canonical Scheduling School")
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
            school_year="2026-2027",
            start_date=date(2026, 8, 20),
            end_date=date(2026, 12, 18),
            ordering=1,
            active=True,
        )
        self.course = Course.objects.create(
            school_id=self.school.id,
            code="MATH-101",
            name="Algebra I",
        )
        self.section = Section.objects.create(
            school_id=self.school.id,
            course=self.course,
            term_ref=self.term,
            term=self.term.code,
        )

        self.household_a = Household.objects.create(
            school_id=self.school.id,
            name="Household A",
        )
        self.household_b = Household.objects.create(
            school_id=self.school.id,
            name="Household B",
        )
        self.student_a = Student.objects.create(
            school_id=self.school.id,
            household=self.household_a,
            first_name="Student",
            last_name="A",
            grade_level="9",
            is_active=True,
        )
        self.student_b = Student.objects.create(
            school_id=self.school.id,
            household=self.household_b,
            first_name="Student",
            last_name="B",
            grade_level="9",
            is_active=True,
        )
        Enrollment.objects.create(
            school_id=self.school.id,
            section=self.section,
            student=self.student_a,
        )

        self.staff_user = UserAccount.objects.create_user(
            username="canonical-staff",
            email="canonical-staff@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=True,
            school=self.school,
        )
        self.parent_user = UserAccount.objects.create_user(
            username="canonical-parent",
            email="canonical-parent@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=False,
            school=self.school,
        )
        Guardian.objects.create(
            school_id=self.school.id,
            household=self.household_a,
            account=self.parent_user,
            first_name="Parent",
            last_name="A",
            email="canonical-parent@example.com",
            is_primary=True,
        )
        self.client = APIClient()

    def test_staff_terms_use_canonical_term_identity(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/terms/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [
            {
                "term_id": str(self.term.id),
                "code": self.term.code,
                "name": self.term.name,
                "start_date": "2026-08-20",
                "end_date": "2026-12-18",
                "active": True,
            }
        ])

    def test_staff_term_sections_use_canonical_section(self):
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get(
            f"/api/terms/{self.term.id}/sections/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["section_id"], str(self.section.id))
        self.assertEqual(body[0]["term"]["term_id"], str(self.term.id))
        self.assertEqual(body[0]["course"]["code"], self.course.code)
        self.assertEqual(body[0]["section_code"], str(self.section.id))

    def test_parent_term_sections_are_canonical_household_scoped(self):
        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get(
            f"/api/terms/{self.term.id}/sections/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["section_id"] for row in response.json()},
            {str(self.section.id)},
        )

    def test_canonical_student_schedule_uses_academics_enrollment(self):
        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get(
            f"/api/students/{self.student_a.id}/schedule/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(len(body), 1)
        self.assertEqual(body[0]["section_id"], str(self.section.id))
        self.assertEqual(body[0]["course"]["code"], self.course.code)

    def test_parent_cannot_read_other_canonical_student_schedule(self):
        self.client.force_authenticate(user=self.parent_user)
        response = self.client.get(
            f"/api/students/{self.student_b.id}/schedule/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 404)
