"""
Attendance Tenant Invariant Tests
==================================
Verifies that section_attendance_submit() enforces canonical tenant isolation,
verified identity resolution, roster membership, and teacher assignment.

Invariants tested:
  1. Missing X-School-Id header with one school role uses authenticated fallback
  2. Cross-tenant section returns 404
  3. Cross-tenant student returns 404
  4. Valid same-tenant, assigned-teacher, enrolled-student request returns 200
"""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Enrollment, Section
from core.models import Family, School, Student, StudentIdentityLink, UserRole
from households.models import Household, Student as CompatibilityStudent

User = get_user_model()


class AttendanceTenantInvariantTests(TestCase):
    """Two-school fixture with explicit canonical attendance authority."""

    def setUp(self):
        self.school_a = School.objects.create(name="Invariant School A")
        self.school_b = School.objects.create(name="Invariant School B")

        self.teacher = User.objects.create_user(
            username="inv_teacher_a",
            email="inv_teacher_a@test.com",
            password="password",
            school=self.school_a,
        )
        UserRole.objects.create(
            school=self.school_a,
            user=self.teacher,
            role_code="TEACHER",
        )

        self.course_a = Course.objects.create(
            school_id=self.school_a.pk,
            code="INV101",
            name="Invariants 101",
        )
        self.course_b = Course.objects.create(
            school_id=self.school_b.pk,
            code="INV101",
            name="Invariants 101",
        )

        self.section_a = Section.objects.create(
            school_id=self.school_a.pk,
            course=self.course_a,
            term="2026-FALL",
            teacher=self.teacher,
            teacher_name="Invariant Teacher",
        )
        self.section_b = Section.objects.create(
            school_id=self.school_b.pk,
            course=self.course_b,
            term="2026-FALL",
        )

        self.family_a = Family.objects.create(
            school=self.school_a,
            family_name="InvFamily A",
        )
        self.family_b = Family.objects.create(
            school=self.school_b,
            family_name="InvFamily B",
        )

        self.student_a = Student.objects.create(
            school=self.school_a,
            family=self.family_a,
            student_number="INVA001",
            first_name="Alice",
            last_name="Adams",
            dob=datetime.date(2010, 1, 1),
        )
        self.student_b = Student.objects.create(
            school=self.school_b,
            family=self.family_b,
            student_number="INVB001",
            first_name="Bob",
            last_name="Baker",
            dob=datetime.date(2010, 2, 2),
        )

        household_a = Household.objects.create(
            school_id=self.school_a.id,
            name="Invariant Household A",
        )
        compatibility_a = CompatibilityStudent.objects.create(
            school_id=self.school_a.id,
            household=household_a,
            first_name="Alice",
            last_name="Adams",
            is_active=True,
        )
        StudentIdentityLink.objects.create(
            school=self.school_a,
            core_student=self.student_a,
            compatibility_student=compatibility_a,
            source=StudentIdentityLink.SOURCE_MANUAL,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference="test:attendance-tenant:a",
        )
        Enrollment.objects.create(
            school_id=self.school_a.id,
            section=self.section_a,
            student=compatibility_a,
        )

        household_b = Household.objects.create(
            school_id=self.school_b.id,
            name="Invariant Household B",
        )
        compatibility_b = CompatibilityStudent.objects.create(
            school_id=self.school_b.id,
            household=household_b,
            first_name="Bob",
            last_name="Baker",
            is_active=True,
        )
        StudentIdentityLink.objects.create(
            school=self.school_b,
            core_student=self.student_b,
            compatibility_student=compatibility_b,
            source=StudentIdentityLink.SOURCE_MANUAL,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            evidence_reference="test:attendance-tenant:b",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.teacher)

    def _url(self, section):
        return f"/api/v1/academics/sections/{section.id}/attendance/"

    def _payload(self, student):
        return {
            "items": [
                {"student_id": str(student.id), "status": "PRESENT"}
            ]
        }

    def test_missing_school_header_uses_single_role_school(self):
        resp = self.client.post(
            self._url(self.section_a),
            self._payload(self.student_a),
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))

    def test_cross_tenant_section_returns_404(self):
        resp = self.client.post(
            self._url(self.section_b),
            self._payload(self.student_a),
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 404)

    def test_cross_tenant_student_returns_404(self):
        resp = self.client.post(
            self._url(self.section_a),
            self._payload(self.student_b),
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 404)

    def test_valid_same_tenant_request_returns_200(self):
        resp = self.client.post(
            self._url(self.section_a),
            self._payload(self.student_a),
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("ok"))
        self.assertEqual(body.get("section_id"), str(self.section_a.id))
