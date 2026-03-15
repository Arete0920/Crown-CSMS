from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from admissions.models import AdmissionsApplication
from core.models import AcademicYear, Family, School, UserAccount
from crown_api.models import Household, Person, Student


class AdmissionsLinksApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )
        self.nonstaff_user = UserAccount.objects.create_user(
            username="normaluser",
            email="normal@example.com",
            password="testpass",
            is_staff=False,
        )

        self.school = School.objects.create(name="Crown Academy")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026–2027",
            start_date=date(2026, 8, 1),
            end_date=date(2027, 6, 15),
            is_current=True,
        )

        self.family = Family.objects.create(school=self.school, family_name="Megahan")

        self.household = Household.objects.create(household_name="The Megahan Family")

        student_person = Person.objects.create(
            first_name="Alice",
            last_name="Megahan",
            email="alice.megahan@student.example.com",
        )
        self.sis_student = Student.objects.create(
            person=student_person,
            household=self.household,
            grade_level="3",
            active=True,
        )

        self.app = AdmissionsApplication.objects.create(
            school=self.school,
            academic_year=self.year,
            family=self.family,
            status=AdmissionsApplication.STATUS_SUBMITTED,
            household=self.household,
            sis_student=self.sis_student,
        )

    def test_staff_can_list_and_detail(self):
        self.client.force_authenticate(user=self.staff_user)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.id))

        resp = self.client.get("/api/admissions/applications/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIsInstance(body, list)
        self.assertEqual(body[0]["id"], self.app.id)
        self.assertEqual(body[0]["household_id"], str(self.household.id))
        self.assertEqual(body[0]["student_id"], str(self.sis_student.id))

        detail = self.client.get(f"/api/admissions/applications/{self.app.id}/")
        self.assertEqual(detail.status_code, 200)
        d = detail.json()
        self.assertEqual(d["id"], self.app.id)
        self.assertEqual(d["household_id"], str(self.household.id))
        self.assertEqual(d["student_id"], str(self.sis_student.id))

    def test_nonstaff_gets_403(self):
        self.client.force_authenticate(user=self.nonstaff_user)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.id))
        resp = self.client.get("/api/admissions/applications/")
        self.assertEqual(resp.status_code, 403)
