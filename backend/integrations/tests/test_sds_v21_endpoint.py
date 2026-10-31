"""Database/API boundary tests for the CROWN Microsoft SDS v2.1 export."""

import csv
import uuid
import zipfile
from io import BytesIO, StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from academics.models import Course, Enrollment, Section, TeacherAssignment, Term
from core.models import (
    AcademicYear,
    CrownPermission,
    RolePermission,
    School,
    Staff,
    UserRole,
)
from households.models import Household, Student

from integrations.sds_v21 import SDS_FILENAMES, sds_v21_export


User = get_user_model()


class SdsV21EndpointTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.school = School.objects.create(name="Fictional Christian Academy")
        self.other_school = School.objects.create(name="Other Fictional School")
        self.year = AcademicYear.objects.create(
            school=self.school,
            name="2026-2027",
            start_date="2026-08-15",
            end_date="2027-05-30",
            is_current=True,
        )
        self.term = Term.objects.create(
            school_id=self.school.id,
            academic_year=self.year,
            code="FALL",
            name="Fall 2026",
            school_year="2026-2027",
            active=True,
        )
        self.course = Course.objects.create(
            school_id=self.school.id,
            code="ENG8",
            name="English 8",
        )
        self.section = Section.objects.create(
            school_id=self.school.id,
            course=self.course,
            term_ref=self.term,
            term=self.term.code,
            grade_band="8",
        )

        self.operator = User.objects.create_user(
            username="registrar@example.invalid",
            email="registrar@example.invalid",
            school=self.school,
            password="not-used",
            is_active=True,
        )
        UserRole.objects.create(
            user=self.operator,
            school=self.school,
            role_code="REGISTRAR",
        )
        permission, _ = CrownPermission.objects.get_or_create(
            code="rosters.edit",
            defaults={"description": "Edit class rosters"},
        )
        RolePermission.objects.get_or_create(
            role_code="REGISTRAR",
            permission=permission,
        )

        self.student_account = User.objects.create_user(
            username="student@example.invalid",
            email="student@example.invalid",
            school=self.school,
            password="not-used",
            is_active=True,
        )
        household = Household.objects.create(
            school_id=self.school.id,
            name="Fictional Household",
        )
        self.student = Student.objects.create(
            school_id=self.school.id,
            household=household,
            account=self.student_account,
            first_name="Ada",
            last_name="Lovelace",
            grade_level="8",
            is_active=True,
        )
        Enrollment.objects.create(
            school_id=self.school.id,
            section=self.section,
            student=self.student,
        )

        self.staff = Staff.objects.create(
            school=self.school,
            first_name="Grace",
            last_name="Hopper",
            email="teacher@example.invalid",
            role_type="TEACHER",
            status="ACTIVE",
        )
        TeacherAssignment.objects.create(
            school_id=self.school.id,
            section=self.section,
            staff=self.staff,
        )

    def _request(self, user=None, *, school=None, term_id=None):
        selected_school = school or self.school
        selected_term = self.term.id if term_id is None else term_id
        request = self.factory.get(
            "/api/integrations/microsoft/sds-v2.1/export/",
            {"term_id": str(selected_term)},
            HTTP_X_SCHOOL_ID=str(selected_school.id),
        )
        force_authenticate(request, user=user or self.operator)
        return request

    def test_authorized_school_export_returns_real_five_file_zip(self):
        response = sds_v21_export(self._request())

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertEqual(response["X-Crown-SDS-School-Id"], str(self.school.id))
        self.assertEqual(response["X-Crown-SDS-Term-Id"], str(self.term.id))
        self.assertEqual(response["X-Crown-SDS-Classes"], "1")
        self.assertEqual(response["X-Crown-SDS-Students"], "1")
        self.assertEqual(response["X-Crown-SDS-Teachers"], "1")

        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            self.assertEqual(tuple(archive.namelist()), SDS_FILENAMES)
            users = list(
                csv.DictReader(
                    StringIO(archive.read("users.csv").decode("utf-8"))
                )
            )
            enrollments = list(
                csv.DictReader(
                    StringIO(archive.read("enrollments.csv").decode("utf-8"))
                )
            )

        self.assertEqual(
            {row["username"] for row in users},
            {"student@example.invalid", "teacher@example.invalid"},
        )
        self.assertEqual(
            {(row["userSourcedId"], row["role"]) for row in enrollments},
            {
                (f"student:{self.student.id}", "student"),
                (f"staff:{self.staff.id}", "teacher"),
            },
        )

    def test_authenticated_user_without_roster_grant_is_forbidden(self):
        unauthorized = User.objects.create_user(
            username="teacher-no-export@example.invalid",
            email="teacher-no-export@example.invalid",
            school=self.school,
            password="not-used",
            is_active=True,
        )

        response = sds_v21_export(self._request(user=unauthorized))

        self.assertEqual(response.status_code, 403)

    def test_other_school_selection_is_denied_by_school_scoped_permission(self):
        response = sds_v21_export(self._request(school=self.other_school))

        self.assertEqual(response.status_code, 404)

    def test_foreign_or_invalid_term_cannot_be_exported(self):
        other_year = AcademicYear.objects.create(
            school=self.other_school,
            name="2026-2027",
            start_date="2026-08-15",
            end_date="2027-05-30",
            is_current=True,
        )
        other_term = Term.objects.create(
            school_id=self.other_school.id,
            academic_year=other_year,
            code="FALL",
            name="Fall 2026",
            active=True,
        )

        response = sds_v21_export(self._request(term_id=other_term.id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "sds_term_invalid")

    def test_selected_term_with_no_classes_fails_closed(self):
        empty_term = Term.objects.create(
            school_id=self.school.id,
            academic_year=self.year,
            code="SPRING",
            name="Spring 2027",
            active=True,
        )

        response = sds_v21_export(self._request(term_id=empty_term.id))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "sds_no_classes")
