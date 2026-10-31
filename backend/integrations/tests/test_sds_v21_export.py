"""Contract tests for the Microsoft SDS v2.1 CSV export helpers."""

import csv
import uuid
import zipfile
from io import BytesIO, StringIO
from types import SimpleNamespace

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from integrations.sds_v21 import (
    SDS_FILENAMES,
    _build_sds_files,
    _zip_sds_files,
)


def _student(student_id, email):
    return SimpleNamespace(
        id=student_id,
        first_name="Ada",
        last_name="Lovelace",
        account=SimpleNamespace(email=email, username=email),
    )


def _staff(staff_id, email):
    return SimpleNamespace(
        id=staff_id,
        first_name="Grace",
        last_name="Hopper",
        email=email,
    )


class SdsV21ExportContractTest(SimpleTestCase):
    def setUp(self):
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000101")
        self.section_id = uuid.UUID("00000000-0000-0000-0000-000000000102")
        self.student_id = uuid.UUID("00000000-0000-0000-0000-000000000103")
        self.staff_id = uuid.UUID("00000000-0000-0000-0000-000000000104")
        self.school = SimpleNamespace(id=self.school_id, name="Fictional Christian Academy")
        self.section = SimpleNamespace(
            id=self.section_id,
            course=SimpleNamespace(code="ENG8", name="English 8"),
            term="2026-FALL",
        )

    def _files(self, *, student_email="student@example.invalid", staff_email="teacher@example.invalid"):
        student = _student(self.student_id, student_email)
        staff = _staff(self.staff_id, staff_email)
        student_enrollment = SimpleNamespace(
            section_id=self.section_id,
            student_id=self.student_id,
            student=student,
        )
        teacher_assignment = SimpleNamespace(
            section_id=self.section_id,
            staff_id=self.staff_id,
            staff=staff,
        )
        return _build_sds_files(
            school=self.school,
            sections=[self.section],
            student_enrollments=[student_enrollment],
            teacher_assignments=[teacher_assignment],
        )

    def test_five_file_package_has_required_sds_headers_and_roles(self):
        files = self._files()

        self.assertEqual(tuple(files), SDS_FILENAMES)

        users = list(csv.DictReader(StringIO(files["users.csv"])))
        roles = list(csv.DictReader(StringIO(files["roles.csv"])))
        classes = list(csv.DictReader(StringIO(files["classes.csv"])))
        enrollments = list(csv.DictReader(StringIO(files["enrollments.csv"])))

        self.assertEqual(
            list(users[0]),
            [
                "sourcedId",
                "username",
                "familyName",
                "givenName",
                "email",
                "userNumber",
            ],
        )
        self.assertEqual({row["role"] for row in roles}, {"student", "teacher"})
        self.assertEqual(classes[0]["orgSourcedId"], f"school:{self.school_id}")
        self.assertEqual(classes[0]["sourcedId"], f"section:{self.section_id}")
        self.assertEqual(
            {(row["userSourcedId"], row["role"]) for row in enrollments},
            {
                (f"student:{self.student_id}", "student"),
                (f"staff:{self.staff_id}", "teacher"),
            },
        )

    def test_identity_matching_is_domain_qualified_and_normalized(self):
        files = self._files(
            student_email="STUDENT@EXAMPLE.INVALID",
            staff_email="TEACHER@EXAMPLE.INVALID",
        )
        users = list(csv.DictReader(StringIO(files["users.csv"])))

        self.assertEqual(
            {row["username"] for row in users},
            {"student@example.invalid", "teacher@example.invalid"},
        )
        self.assertTrue(all(row["email"] == row["username"] for row in users))

    def test_missing_domain_qualified_identity_fails_closed(self):
        with self.assertRaises(ValidationError) as error:
            self._files(student_email="local-student")

        self.assertEqual(error.exception.detail["code"], "sds_identity_missing")

    def test_duplicate_cloud_username_fails_closed(self):
        shared = "same@example.invalid"
        with self.assertRaises(ValidationError) as error:
            self._files(student_email=shared, staff_email=shared)

        self.assertEqual(error.exception.detail["code"], "sds_identity_ambiguous")

    def test_zip_is_real_deterministic_zip_with_exact_file_set(self):
        files = self._files()

        first = _zip_sds_files(files)
        second = _zip_sds_files(files)

        self.assertEqual(first, second)
        self.assertTrue(first.startswith(b"PK"))
        with zipfile.ZipFile(BytesIO(first)) as archive:
            self.assertEqual(tuple(archive.namelist()), SDS_FILENAMES)
            for filename in SDS_FILENAMES:
                payload = archive.read(filename).decode("utf-8")
                self.assertNotIn("\n\n", payload)
