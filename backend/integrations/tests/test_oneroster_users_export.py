"""Regression proof for OneRoster users.csv completeness and tenant scoping."""

import csv
import uuid
from io import StringIO
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from integrations.oneroster import _build_users, oneroster_export_bundle


class OneRosterUsersBuilderTest(SimpleTestCase):
    def setUp(self):
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000011")
        self.student_id = uuid.UUID("00000000-0000-0000-0000-000000000012")

    def test_users_csv_contains_enrollment_reference_fields(self):
        student = SimpleNamespace(
            id=self.student_id,
            first_name="Ada",
            last_name="Lovelace",
            grade_level="10",
            is_active=True,
        )

        filename, content = _build_users(self.school_id, [student])
        rows = list(csv.DictReader(StringIO(content)))

        self.assertEqual(filename, "users.csv")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sourcedId"], str(self.student_id))
        self.assertEqual(rows[0]["orgSourcedIds"], str(self.school_id))
        self.assertEqual(rows[0]["role"], "student")
        self.assertEqual(rows[0]["givenName"], "Ada")
        self.assertEqual(rows[0]["familyName"], "Lovelace")
        self.assertEqual(rows[0]["grades"], "10")
        self.assertEqual(rows[0]["enabledUser"], "true")

    def test_inactive_student_is_not_exported_as_enabled(self):
        student = SimpleNamespace(
            id=self.student_id,
            first_name="Grace",
            last_name="Hopper",
            grade_level="12",
            is_active=False,
        )

        _, content = _build_users(self.school_id, [student])
        row = next(csv.DictReader(StringIO(content)))

        self.assertEqual(row["status"], "tobedeleted")
        self.assertEqual(row["enabledUser"], "false")


class OneRosterBundleUsersContractTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000021")
        self.user = SimpleNamespace(
            is_authenticated=True,
            is_active=True,
            is_staff=True,
            is_superuser=False,
        )

    def test_bundle_queries_only_enrolled_students_for_tenant_and_emits_users_first(self):
        request = self.factory.get("/api/integrations/oneroster/export/")
        force_authenticate(request, user=self.user)

        school = SimpleNamespace(id=self.school_id, name="Heritage Christian Academy")
        ordered_students = []
        distinct_qs = MagicMock()
        distinct_qs.order_by.return_value = ordered_students
        student_qs = MagicMock()
        student_qs.distinct.return_value = distinct_qs
        empty_qs = MagicMock()
        empty_qs.order_by.return_value = []
        empty_qs.select_related.return_value = empty_qs

        with (
            patch("integrations.oneroster.get_request_school_id", return_value=self.school_id),
            patch("integrations.oneroster.School.objects.get", return_value=school),
            patch("integrations.oneroster.Term.objects.filter", return_value=empty_qs),
            patch("integrations.oneroster.Course.objects.filter", return_value=empty_qs),
            patch("integrations.oneroster.Section.objects.filter", return_value=empty_qs),
            patch("integrations.oneroster.Student.objects.filter", return_value=student_qs) as student_filter,
            patch("integrations.oneroster.Enrollment.objects.filter", return_value=empty_qs),
        ):
            response = oneroster_export_bundle(request)

        self.assertEqual(response.status_code, 200)
        student_filter.assert_called_once_with(
            school_id=self.school_id,
            enrollments__school_id=self.school_id,
        )
        student_qs.distinct.assert_called_once_with()
        distinct_qs.order_by.assert_called_once_with("last_name", "first_name", "id")

        body = response.content.decode("utf-8")
        self.assertIn('filename="users.csv"', body)
        self.assertIn('filename="enrollments.csv"', body)
        self.assertLess(body.index('filename="users.csv"'), body.index('filename="enrollments.csv"'))
        self.assertEqual(body.count("Content-Type: text/csv; charset=utf-8"), 6)

    def test_non_staff_user_remains_forbidden(self):
        request = self.factory.get("/api/integrations/oneroster/export/")
        force_authenticate(
            request,
            user=SimpleNamespace(
                is_authenticated=True,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            ),
        )

        response = oneroster_export_bundle(request)

        self.assertEqual(response.status_code, 403)
