import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section, TeacherAssignment
from core.models import Family, School, Staff, Student, StudentIdentityLink, UserRole
from households.models import Household, Student as CompatibilityStudent

User = get_user_model()


class AttendanceAssignmentGuardTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Attendance Guard School")

        self.staff_assigned = Staff.objects.create(
            school=self.school,
            first_name="Assigned",
            last_name="Teacher",
            email="assigned.teacher@test.com",
            role_type="TEACHER",
        )
        self.staff_unassigned = Staff.objects.create(
            school=self.school,
            first_name="Unassigned",
            last_name="Teacher",
            email="unassigned.teacher@test.com",
            role_type="TEACHER",
        )

        self.assigned_teacher = User.objects.create_user(
            username="assigned_teacher",
            email="assigned.teacher@test.com",
            password="password",
            school=self.school,
            staff=self.staff_assigned,
        )
        self.unassigned_teacher = User.objects.create_user(
            username="unassigned_teacher",
            email="unassigned.teacher@test.com",
            password="password",
            school=self.school,
            staff=self.staff_unassigned,
        )
        self.admin_user = User.objects.create_user(
            username="attendance_registrar",
            email="attendance.registrar@test.com",
            password="password",
            school=self.school,
        )

        UserRole.objects.create(user=self.assigned_teacher, school=self.school, role_code="TEACHER")
        UserRole.objects.create(user=self.unassigned_teacher, school=self.school, role_code="TEACHER")
        UserRole.objects.create(user=self.admin_user, school=self.school, role_code="REGISTRAR")

        self.course = Course.objects.create(
            school_id=self.school.id,
            code="ATT-101",
            name="Attendance 101",
        )
        self.section = Section.objects.create(
            school_id=self.school.id,
            course=self.course,
            term="2026-FALL",
            teacher=self.assigned_teacher,
            teacher_name="Assigned Teacher",
        )
        TeacherAssignment.objects.create(
            school_id=self.school.id,
            section=self.section,
            staff=self.staff_assigned,
        )

        family = Family.objects.create(school=self.school, family_name="Attendance Family")
        self.student = Student.objects.create(
            school=self.school,
            family=family,
            student_number="ATT001",
            first_name="Alice",
            last_name="Attendance",
            dob=datetime.date(2011, 1, 1),
        )
        household = Household.objects.create(
            school_id=self.school.id,
            name="Attendance Household",
        )
        self.compatibility_student = CompatibilityStudent.objects.create(
            school_id=self.school.id,
            household=household,
            first_name="Alice",
            last_name="Attendance",
            is_active=True,
        )
        StudentIdentityLink.objects.create(
            school=self.school,
            core_student=self.student,
            compatibility_student=self.compatibility_student,
            source=StudentIdentityLink.SOURCE_MANUAL,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference="test:attendance-assignment-guard",
        )
        Enrollment.objects.create(
            school_id=self.school.id,
            section=self.section,
            student=self.compatibility_student,
        )

        self.url = f"/api/v1/academics/sections/{self.section.id}/attendance/"
        self.payload = {
            "date": datetime.date.today().isoformat(),
            "items": [{"student_id": str(self.student.id), "status": "PRESENT"}],
        }

    def test_assigned_teacher_can_submit_attendance(self):
        client = APIClient()
        client.force_authenticate(user=self.assigned_teacher)

        resp = client.post(self.url, self.payload, format="json", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("section_id"), str(self.section.id))

    def test_unassigned_teacher_is_forbidden(self):
        client = APIClient()
        client.force_authenticate(user=self.unassigned_teacher)

        resp = client.post(self.url, self.payload, format="json", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 403)
        self.assertIn("assigned teacher", (resp.json().get("detail") or "").lower())

    def test_admin_can_submit_without_teacher_assignment(self):
        client = APIClient()
        client.force_authenticate(user=self.admin_user)

        resp = client.post(self.url, self.payload, format="json", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))
