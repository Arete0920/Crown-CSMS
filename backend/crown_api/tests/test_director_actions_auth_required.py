from __future__ import annotations

import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from aid.models import AidAward
from audit.models import AuditLog
from core.models import AcademicYear, Family, School, Student, UserRole
from finance.models import ChartAccount


class DirectorActionsAuthRequiredTests(TestCase):
    def test_director_actions_requires_auth_and_school_scoped_director_role(self):
        school = School.objects.create(name="Auth Test School")
        other_school = School.objects.create(name="Other Auth Test School")
        year = AcademicYear.objects.create(
            school=school,
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 10),
            is_current=True,
        )

        ChartAccount.objects.get_or_create(
            school=school,
            code="AID",
            defaults={"name": "Financial Aid", "account_type": "INCOME", "is_active": True},
        )

        family = Family.objects.create(school=school, family_name="Auth Test Family")
        student = Student.objects.create(
            school=school,
            family=family,
            student_number="S10000",
            first_name="Test",
            last_name="Student",
            dob=date(2010, 1, 1),
        )

        award = AidAward.objects.create(
            school=school,
            student=student,
            academic_year=year,
            awarded_cents=50000,
            decision_status=AidAward.DECISION_ACCEPTED,
        )

        payload = {
            "action": "POST_ACCEPTED_AWARDS",
            "school_id": str(school.id),
            "year_id": str(year.id),
            "ids": [str(award.id)],
        }

        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(resp.status_code, 401)
        self.assertTrue(
            AuditLog.objects.filter(
                action="POST",
                model="/api/director/actions/",
                metadata__status_code=401,
            ).exists()
        )

        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        User = get_user_model()
        nonstaff = User.objects.create_user(
            username="director_actions_nonstaff",
            email="director_actions_nonstaff@test.com",
            password="password123",
        )
        self.client.force_login(nonstaff)
        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(
            AuditLog.objects.filter(
                user_id=nonstaff.id,
                action="POST",
                model="/api/director/actions/",
                metadata__status_code=403,
            ).exists()
        )

        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        staff = User.objects.create_user(
            username="director_actions_staff",
            email="director_actions_staff@test.com",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(staff)
        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(resp.status_code, 403)

        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        UserRole.objects.create(user=staff, school=other_school, role_code="AID_DIRECTOR")
        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(resp.status_code, 403)

        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        UserRole.objects.create(user=staff, school=school, role_code="AID_DIRECTOR")
        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(resp.status_code, 200)

        award.refresh_from_db()
        self.assertIsNotNone(award.ledger_entry_id)

    def test_director_actions_rejects_mismatched_tenant_header(self):
        school = School.objects.create(name="Header Target School")
        other_school = School.objects.create(name="Header Other School")
        User = get_user_model()
        staff = User.objects.create_user(
            username="director_actions_header_staff",
            email="director_actions_header_staff@test.com",
            password="password123",
            is_staff=True,
        )
        UserRole.objects.create(user=staff, school=school, role_code="AID_DIRECTOR")
        self.client.force_login(staff)

        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(
                {"action": "POST_ACCEPTED_AWARDS", "school_id": str(school.id), "ids": ["1"]}
            ),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(other_school.id),
        )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["detail"], "X-School-Id must match the request school_id.")

    def test_director_actions_options_reaches_drf(self):
        resp = self.client.options("/api/director/actions/")
        self.assertNotIn(resp.status_code, {400, 403})
        self.assertFalse(
            AuditLog.objects.filter(action="OPTIONS", model="/api/director/actions/").exists()
        )
