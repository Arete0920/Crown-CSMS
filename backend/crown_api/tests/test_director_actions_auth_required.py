from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from django.test import TestCase
from rest_framework.test import APIClient

from aid.models import AidAuditEvent, AidAward
from audit.models import AuditLog
from core.models import AcademicYear, Family, HouseholdFamilyLink, LedgerEntry, School, Student, UserRole
from households.models import Household
from ledger.models import Credit, Payment
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
        # Multiple role-derived schools without an unambiguous principal
        # school must not provide implicit cross-school selection authority.
        ambiguous = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(ambiguous.status_code, 403)
        award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)

        # Establish an explicit principal school and a matching school role.
        staff.school = school
        staff.save(update_fields=["school"])
        resp = self.client.post(
            "/api/director/actions/",
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(resp.status_code, 200)

        award.refresh_from_db()
        self.assertIsNotNone(award.ledger_entry_id)
        self.assertEqual(resp.json()["posted_count"], 1)
        self.assertIsNone(resp.json()["errors"])
        self.assertEqual(
            AidAuditEvent.objects.filter(
                school=school, entity_id=str(award.id),
                action="STUDENT_ACCOUNT_CREDIT_DEFERRED",
            ).count(), 1,
        )
        self.assertFalse(Credit.objects.filter(school_id=school.id).exists())
        self.assertFalse(Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists())

    def test_director_posts_non_cash_credit_once_with_verified_family_link(self):
        school = School.objects.create(name="Credit Director School")
        year = AcademicYear.objects.create(
            school=school, name="2026-27",
            start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
        )
        family = Family.objects.create(school=school, family_name="Credit Family")
        student = Student.objects.create(
            school=school, family=family, student_number="SC-1",
            first_name="Sample", last_name="Student", dob=date(2012, 1, 1),
        )
        household = Household.objects.create(school_id=school.id, name="Credit Household")
        HouseholdFamilyLink.objects.create(
            school=school, family=family, household_id=household.id,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
        ChartAccount.objects.create(
            school=school, code="AID", name="Aid", account_type="INCOME",
        )
        award = AidAward.objects.create(
            school=school, academic_year=year, student=student,
            awarded_cents=50000, decision_status=AidAward.DECISION_ACCEPTED,
        )
        User = get_user_model()
        director = User.objects.create_user(
            username="director_credit_verified", password="synthetic",
            is_staff=True, school=school,
        )
        UserRole.objects.create(user=director, school=school, role_code="AID_DIRECTOR")
        self.client.force_login(director)
        payload = {
            "action": "POST_ACCEPTED_AWARDS",
            "school_id": str(school.id),
            "year_id": str(year.id),
            "ids": [str(award.id)],
        }
        def post_action():
            return self.client.post(
                "/api/director/actions/", data=json.dumps(payload),
                content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id),
            )

        first = post_action()
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["posted_count"], 1)
        self.assertIsNone(first.json()["errors"])
        award.refresh_from_db()
        self.assertIsNotNone(award.ledger_entry_id)
        credit = Credit.objects.get(
            school_id=school.id, source=Credit.SOURCE_FINANCIAL_AID,
            reference=f"aid_award:{award.id}",
        )
        self.assertEqual(credit.amount, Decimal("500.00"))
        self.assertEqual(credit.account.household_id, household.id)
        self.assertFalse(Payment.objects.filter(
            school_id=school.id, source="FINANCIAL_AID",
        ).exists())

        second = post_action()
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()["posted_count"], 0)
        self.assertIsNone(second.json()["errors"])
        self.assertEqual(
            Credit.objects.filter(school_id=school.id, source=Credit.SOURCE_FINANCIAL_AID).count(), 1
        )
        self.assertEqual(LedgerEntry.objects.filter(school=school, student=student).count(), 1)
        self.assertEqual(
            AidAuditEvent.objects.filter(
                school=school, entity_id=str(award.id),
                action="STUDENT_ACCOUNT_CREDIT_POSTED",
            ).count(), 1,
        )
        # Duplicate identifiers in one request must not issue another credit.
        payload["ids"] = [str(award.id), str(award.id)]
        repeated = post_action()
        self.assertEqual(repeated.status_code, 200)
        self.assertEqual(repeated.json()["posted_count"], 0)
        self.assertIsNone(repeated.json()["errors"])
        self.assertEqual(Credit.objects.filter(
            school_id=school.id, source=Credit.SOURCE_FINANCIAL_AID,
        ).count(), 1)
        self.assertEqual(LedgerEntry.objects.filter(
            school=school, student=student,
        ).count(), 1)

    def test_credit_projection_error_rolls_back_legacy_post(self):
        school = School.objects.create(name="Rollback Director School")
        year = AcademicYear.objects.create(
            school=school, name="2026-27",
            start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
        )
        family = Family.objects.create(school=school, family_name="Rollback Family")
        student = Student.objects.create(
            school=school, family=family, student_number="SR-1",
            first_name="Sample", last_name="Student", dob=date(2012, 1, 1),
        )
        ChartAccount.objects.create(
            school=school, code="AID", name="Aid", account_type="INCOME",
        )
        award = AidAward.objects.create(
            school=school, academic_year=year, student=student,
            awarded_cents=50000, decision_status=AidAward.DECISION_ACCEPTED,
        )
        good_award = AidAward.objects.create(
            school=school, academic_year=year, student=student,
            awarded_cents=25000, decision_status=AidAward.DECISION_ACCEPTED,
        )
        User = get_user_model()
        director = User.objects.create_user(
            username="director_credit_rollback", password="synthetic",
            is_staff=True, school=school,
        )
        UserRole.objects.create(user=director, school=school, role_code="AID_DIRECTOR")
        self.client.force_login(director)
        payload = {
            "action": "POST_ACCEPTED_AWARDS",
            "school_id": str(school.id),
            "year_id": str(year.id),
            "ids": [str(award.id), str(good_award.id)],
        }
        from aid.services.ledger_bridge import ensure_accepted_award_credit as real_ensure
        failed_award_pk = award.pk

        def selective_projection_failure(*, award, actor_user):
            if award.pk == failed_award_pk:
                raise RuntimeError("synthetic credit projection failure")
            return real_ensure(award=award, actor_user=actor_user)

        with patch(
            "crown_api.director_views.ensure_accepted_award_credit",
            side_effect=selective_projection_failure,
        ):
            failed = self.client.post(
                "/api/director/actions/", data=json.dumps(payload),
                content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id),
            )
        self.assertEqual(failed.status_code, 200)
        self.assertEqual(failed.json()["posted_count"], 1)
        self.assertEqual(
            failed.json()["errors"],
            [{"award_id": str(award.id), "error": "Internal processing error"}],
        )
        award.refresh_from_db()
        good_award.refresh_from_db()
        self.assertIsNone(award.ledger_entry_id)
        self.assertIsNotNone(good_award.ledger_entry_id)
        self.assertEqual(LedgerEntry.objects.filter(school=school, student=student).count(), 1)
        self.assertFalse(AidAuditEvent.objects.filter(
            school=school, entity_id=str(award.id), action="LEDGER_POSTED",
        ).exists())

        payload["ids"] = [str(award.id)]
        retried = self.client.post(
            "/api/director/actions/", data=json.dumps(payload),
            content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(retried.status_code, 200)
        self.assertEqual(retried.json()["posted_count"], 1)
        self.assertIsNone(retried.json()["errors"])
        award.refresh_from_db()
        self.assertIsNotNone(award.ledger_entry_id)
        self.assertEqual(LedgerEntry.objects.filter(school=school, student=student).count(), 2)

    def test_invalid_award_school_links_and_nonpositive_amount_fail_closed(self):
        school = School.objects.create(name="Award integrity school")
        other = School.objects.create(name="Unrelated award school")
        year = AcademicYear.objects.create(
            school=school, name="2026-27",
            start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
        )
        other_year = AcademicYear.objects.create(
            school=other, name="2026-27-other",
            start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
        )
        family = Family.objects.create(school=school, family_name="Valid family")
        student = Student.objects.create(
            school=school, family=family, student_number="I-1",
            first_name="Valid", last_name="Student", dob=date(2011, 1, 1),
        )
        foreign_family = Family.objects.create(
            school=other, family_name="Foreign family",
        )
        foreign_student = Student.objects.create(
            school=other, family=foreign_family, student_number="I-2",
            first_name="Foreign", last_name="Student", dob=date(2011, 1, 1),
        )
        ChartAccount.objects.create(
            school=school, code="AID", name="Aid", account_type="INCOME",
        )
        awards = [
            AidAward.objects.create(
                school=school, academic_year=other_year, student=student,
                awarded_cents=3000, decision_status=AidAward.DECISION_ACCEPTED,
            ),
            AidAward.objects.create(
                school=school, academic_year=year, student=foreign_student,
                awarded_cents=3000, decision_status=AidAward.DECISION_ACCEPTED,
            ),
            AidAward.objects.create(
                school=school, academic_year=year, student=student,
                awarded_cents=0, decision_status=AidAward.DECISION_ACCEPTED,
            ),
            AidAward.objects.create(
                school=school, academic_year=year, student=student,
                awarded_cents=-500, decision_status=AidAward.DECISION_ACCEPTED,
            ),
        ]
        User = get_user_model()
        actor = User.objects.create_user(
            username="director_award_integrity", password="synthetic",
            school=school, is_staff=True,
        )
        UserRole.objects.create(user=actor, school=school, role_code="AID_DIRECTOR")
        self.client.force_login(actor)
        payload = {
            "action": "POST_ACCEPTED_AWARDS",
            "school_id": str(school.id),
            "ids": [str(award.id) for award in awards],
        }
        response = self.client.post(
            "/api/director/actions/", data=json.dumps(payload),
            content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["posted_count"], 0)
        self.assertEqual(
            [error["award_id"] for error in response.json()["errors"]],
            [str(award.id) for award in awards],
        )
        self.assertTrue(all(
            error["error"] == "Internal processing error"
            for error in response.json()["errors"]
        ))
        for award in awards:
            award.refresh_from_db()
            self.assertIsNone(award.ledger_entry_id)
        self.assertFalse(LedgerEntry.objects.filter(school=school).exists())
        self.assertFalse(Credit.objects.filter(school_id=school.id).exists())
        self.assertFalse(Payment.objects.filter(school_id=school.id).exists())
        self.assertFalse(AidAuditEvent.objects.filter(
            school=school, action="LEDGER_POSTED",
        ).exists())

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

    def test_retired_force_seed_http_route_is_unresolvable_on_both_api_mounts(self):
        with self.assertRaises(NoReverseMatch):
            reverse("force_seed_user")
        for path in ("/api/director/force_seed_user/", "/api/v1/director/force_seed_user/"):
            with self.subTest(path=path), self.assertRaises(Resolver404):
                resolve(path)
