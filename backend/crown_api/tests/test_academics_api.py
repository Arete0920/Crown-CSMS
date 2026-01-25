from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount
from crown_api.models import (
    AttendanceRecord,
    Course,
    GradeRecord,
    Household,
    HouseholdMember,
    Person,
    Student,
    UserPersonLink,
)
from crown_api.models_households import ROLE_GUARDIAN


class AcademicsApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password="testpass",
            is_staff=True,
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password="testpass",
            is_staff=False,
        )

        self.household_a = Household.objects.create(household_name="Household A")
        self.household_b = Household.objects.create(household_name="Household B")

        self.parent_person = Person.objects.create(
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
        )
        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
        HouseholdMember.objects.create(
            household=self.household_a,
            person=self.parent_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        self.student_a_person = Person.objects.create(
            first_name="Student",
            last_name="A",
            email="student.a@example.com",
        )
        self.student_b_person = Person.objects.create(
            first_name="Student",
            last_name="B",
            email="student.b@example.com",
        )

        self.student_a = Student.objects.create(
            person=self.student_a_person,
            household=self.household_a,
            grade_level="3",
            active=True,
        )
        self.student_b = Student.objects.create(
            person=self.student_b_person,
            household=self.household_b,
            grade_level="5",
            active=True,
        )

        self.course_math = Course.objects.create(course_code="MATH-101", name="Math")

        AttendanceRecord.objects.create(
            student=self.student_a,
            course=self.course_math,
            date=date(2026, 1, 1),
            status=AttendanceRecord.STATUS_PRESENT,
        )
        AttendanceRecord.objects.create(
            student=self.student_b,
            course=self.course_math,
            date=date(2026, 1, 1),
            status=AttendanceRecord.STATUS_ABSENT,
        )

        GradeRecord.objects.create(
            student=self.student_a,
            course=self.course_math,
            period="Q1",
            assignment_name="Quiz 1",
            score=95,
            score_max=100,
            letter_grade="A",
        )
        GradeRecord.objects.create(
            student=self.student_b,
            course=self.course_math,
            period="Q1",
            assignment_name="Quiz 1",
            score=80,
            score_max=100,
            letter_grade="B",
        )

    def test_attendance_staff_can_access_any_student(self):
        self.client.force_authenticate(user=self.staff_user)

        resp_a = self.client.get(f"/api/students/{self.student_a.id}/attendance/")
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual(len(resp_a.json()), 1)

        resp_b = self.client.get(f"/api/students/{self.student_b.id}/attendance/")
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual(len(resp_b.json()), 1)

    def test_attendance_parent_scoped_and_no_existence_leak(self):
        self.client.force_authenticate(user=self.parent_user)

        ok = self.client.get(f"/api/students/{self.student_a.id}/attendance/")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(len(ok.json()), 1)

        no = self.client.get(f"/api/students/{self.student_b.id}/attendance/")
        self.assertEqual(no.status_code, 404)

    def test_grades_staff_can_access_any_student(self):
        self.client.force_authenticate(user=self.staff_user)

        resp_a = self.client.get(f"/api/students/{self.student_a.id}/grades/")
        self.assertEqual(resp_a.status_code, 200)
        self.assertEqual(len(resp_a.json()), 1)

        resp_b = self.client.get(f"/api/students/{self.student_b.id}/grades/")
        self.assertEqual(resp_b.status_code, 200)
        self.assertEqual(len(resp_b.json()), 1)

    def test_grades_parent_scoped_and_no_existence_leak(self):
        self.client.force_authenticate(user=self.parent_user)

        ok = self.client.get(f"/api/students/{self.student_a.id}/grades/")
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(len(ok.json()), 1)

        no = self.client.get(f"/api/students/{self.student_b.id}/grades/")
        self.assertEqual(no.status_code, 404)

    def test_academics_unauth_401(self):
        resp = self.client.get(f"/api/students/{self.student_a.id}/attendance/")
        self.assertEqual(resp.status_code, 401)

        resp2 = self.client.get(f"/api/students/{self.student_a.id}/grades/")
        self.assertEqual(resp2.status_code, 401)
