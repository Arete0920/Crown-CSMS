from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserAccount, School, Family, Student
from crown_api.models import (
    AttendanceRecord,
    Course,
    GradeRecord,
    Household,
    HouseholdMember,
    Person,
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

        # Create core School and Family for core.models.Student
        self.school = School.objects.create(name="Test School")
        self.family_a = Family.objects.create(school=self.school, family_name="Family A")
        self.family_b = Family.objects.create(school=self.school, family_name="Family B")

        # Create core.models.Student objects
        self.student_a = Student.objects.create(
            school=self.school,
            family=self.family_a,
            student_number="STU001",
            first_name="Student",
            last_name="A",
            dob=date(2018, 1, 1),
            status='ACTIVE',
        )
        self.student_b = Student.objects.create(
            school=self.school,
            family=self.family_b,
            student_number="STU002",
            first_name="Student",
            last_name="B",
            dob=date(2016, 1, 1),
            status='ACTIVE',
        )
        
        # Link families to households for parent scoping
        # Create AdmissionsApplication records to establish the family←→household link
        from admissions.models import AdmissionsApplication
        from core.models import AcademicYear
        from datetime import datetime
        ay = AcademicYear.objects.create(
            school=self.school,
            name="2026",
            start_date=datetime(2026, 1, 1).date(),
            end_date=datetime(2026, 12, 31).date(),
            is_current=True,
        )
        AdmissionsApplication.objects.create(
            school=self.school,
            academic_year=ay,
            family=self.family_a,
            student=self.student_a,
            household=self.household_a,
        )
        AdmissionsApplication.objects.create(
            school=self.school,
            academic_year=ay,
            family=self.family_b,
            student=self.student_b,
            household=self.household_b,
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

    def test_academics_unauth_403(self):
        # IsAuthenticated + JWT configured → DRF emits 401 (not 403) for unauthenticated
        resp = self.client.get(f"/api/students/{self.student_a.id}/attendance/")
        self.assertEqual(resp.status_code, 401)

        resp2 = self.client.get(f"/api/students/{self.student_a.id}/grades/")
        self.assertEqual(resp2.status_code, 401)
