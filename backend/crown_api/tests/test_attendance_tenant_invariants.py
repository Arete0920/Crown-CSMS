"""
Attendance Tenant Invariant Tests
==================================
Verifies that section_attendance_submit() enforces tenant isolation after
the ATTENDANCE_HARDENING_V2 patch (get_request_school_id required=True,
school-scoped Section fetch, student ownership check).

Invariants tested:
  1. Missing X-School-Id header       → 400 (required=True now enforced)
  2. Cross-tenant section (school_b)  → 404 (school_id constraint on Section fetch)
  3. Cross-tenant student (school_b)  → 404 (student ownership check before write)
  4. Valid same-tenant request        → 200 {"ok": true}
"""
import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from academics.models import Course, Section
from core.models import Family, School, Student, UserRole

User = get_user_model()


class AttendanceTenantInvariantTests(TestCase):
    """
    Two-school fixture; teacher is only enrolled at school_a.
    All four invariants must hold after ATTENDANCE_HARDENING_V2.
    """

    def setUp(self):
        # Two isolated schools
        self.school_a = School.objects.create(name="Invariant School A")
        self.school_b = School.objects.create(name="Invariant School B")

        # Teacher at school_a only
        self.teacher = User.objects.create_user(
            username="inv_teacher_a",
            email="inv_teacher_a@test.com",
            password="password",
        )
        UserRole.objects.create(
            school=self.school_a,
            user=self.teacher,
            role_code="TEACHER",
        )

        # Courses (school_id is a plain UUID field, not FK)
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

        # Sections
        self.section_a = Section.objects.create(
            school_id=self.school_a.pk,
            course=self.course_a,
            term="2026-FALL",
        )
        self.section_b = Section.objects.create(
            school_id=self.school_b.pk,
            course=self.course_b,
            term="2026-FALL",
        )

        # Families (required by Student)
        self.family_a = Family.objects.create(
            school=self.school_a,
            family_name="InvFamily A",
        )
        self.family_b = Family.objects.create(
            school=self.school_b,
            family_name="InvFamily B",
        )

        # Students — one per school
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

        self.client = APIClient()
        self.client.force_authenticate(user=self.teacher)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _url(self, section):
        return f"/api/v1/academics/sections/{section.id}/attendance/"

    def _payload(self, student):
        return {
            "items": [
                {"student_id": str(student.id), "status": "PRESENT"}
            ]
        }

    # ------------------------------------------------------------------
    # Invariant 1: missing tenant header → 400
    # ------------------------------------------------------------------

    def test_missing_school_header_returns_400(self):
        """Omitting X-School-Id must return 400 now that required=True is enforced."""
        resp = self.client.post(
            self._url(self.section_a),
            self._payload(self.student_a),
            format="json",
            # No HTTP_X_SCHOOL_ID header
        )
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # Invariant 2: cross-tenant section → 404
    # ------------------------------------------------------------------

    def test_cross_tenant_section_returns_404(self):
        """section_b belongs to school_b; caller asserts school_a → 404."""
        resp = self.client.post(
            self._url(self.section_b),
            self._payload(self.student_a),
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 404)

    # ------------------------------------------------------------------
    # Invariant 3: cross-tenant student → 404
    # ------------------------------------------------------------------

    def test_cross_tenant_student_returns_404(self):
        """student_b is in school_b; writing into school_a's section must fail."""
        resp = self.client.post(
            self._url(self.section_a),
            self._payload(self.student_b),
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_a.pk),
        )
        self.assertEqual(resp.status_code, 404)

    # ------------------------------------------------------------------
    # Invariant 4: valid same-tenant request → 200
    # ------------------------------------------------------------------

    def test_valid_same_tenant_request_returns_200(self):
        """Canonical happy-path: teacher, section, and student all in school_a."""
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
