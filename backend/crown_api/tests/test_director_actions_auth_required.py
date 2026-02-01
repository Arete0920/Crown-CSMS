from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from aid.models import AidAward
from core.models import AcademicYear, Family, School, Student
from finance.models import ChartAccount


class DirectorActionsAuthRequiredTests(TestCase):
    def test_director_actions_requires_auth_and_staff(self):
        school = School.objects.create(name="Auth Test School")
        year = AcademicYear.objects.create(
            school=school,
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 10),
            is_current=True,
        )

        # Required for mark_accepted_and_post()
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

        # 1) Unauthenticated -> 401
        resp = self.client.post("/api/director/actions/", data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, 401)

        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        # 2) Authenticated but non-staff -> 403
        User = get_user_model()
        nonstaff = User.objects.create_user(
            username="director_actions_nonstaff",
            email="director_actions_nonstaff@test.com",
            password="password123",
        )
        self.client.force_login(nonstaff)
        resp = self.client.post("/api/director/actions/", data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, 403)

        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        # 3) Staff -> 200
        staff = User.objects.create_user(
            username="director_actions_staff",
            email="director_actions_staff@test.com",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(staff)
        resp = self.client.post("/api/director/actions/", data=payload, content_type="application/json")
        self.assertEqual(resp.status_code, 200)

        award.refresh_from_db()
        self.assertIsNotNone(award.ledger_entry_id)

    @override_settings(CROWN_ENV="dev", DEV_SEED_KEY="test-dev-seed-key")
    def test_force_seed_user_security(self):
        """Regression test for force_seed_user endpoint security."""
        url = "/api/director/force_seed_user/"

        # 1) Outside dev -> 404
        with override_settings(CROWN_ENV="prod"):
            resp = self.client.post(url)
            self.assertEqual(resp.status_code, 404)

        # 2) In dev, anonymous POST -> 403
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.json(), {"detail": "Forbidden."})

        # 3) Wrong key -> 403
        resp = self.client.post(url, headers={"X-Dev-Seed-Key": "wrong-key"})
        self.assertEqual(resp.status_code, 403)

        # 4) Correct key -> 200, no credentials in response
        resp = self.client.post(url, headers={"X-Dev-Seed-Key": "test-dev-seed-key"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIs(data["ok"], True)
        self.assertNotIn("password", str(data).lower())
        self.assertNotIn("Crown2026!", str(data))
        self.assertTrue("admin" not in str(data).lower() or "admin_created" in data)

        # 5) JWT staff -> 200
        User = get_user_model()
        staff = User.objects.create_user(
            username="seed_staff",
            password="password123",
            is_staff=True,
        )
        self.client.force_login(staff)
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 200)
        self.client.logout()

    @override_settings(CROWN_ENV="prod", DEV_SEED_KEY="test-dev-seed-key")
    def test_force_seed_user_prod_always_404(self):
        """Absolute deny: force_seed_user returns 404 in prod even with valid key."""
        resp = self.client.post(
            "/api/director/force_seed_user/", headers={"X-Dev-Seed-Key": "test-dev-seed-key"}
        )
        self.assertEqual(resp.status_code, 404)
