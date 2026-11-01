"""
Aid Phase 7.5 API Endpoint Tests
==================================
Integration tests for admin_aid_overview, admin_recommend_award,
admin_approve_award, and family_aid_status.

All tests use Django TestCase (not pytest) for consistent discovery via
  python manage.py test aid.tests.test_aid_api

Fixtures built in-process; no external seed data required.
"""

import json
from datetime import date

from django.test import TestCase

from aid.models import AidApplication, AidAward, AidBudgetTracker, AidPolicy
from core.models import AcademicYear, CrownPermission, Family, RolePermission, School, Student, UserAccount, UserRole
from finance.models import ChartAccount


# ---------------------------------------------------------------------------
# Shared fixture factory
# ---------------------------------------------------------------------------

def _make_school(name="Test School"):
    return School.objects.create(name=name)


def _make_ay(school, name="2026-27"):
    return AcademicYear.objects.create(
        school=school,
        name=name,
        start_date=date(2026, 8, 1),
        end_date=date(2027, 5, 31),
    )


def _make_family(school, family_name="Doe"):
    return Family.objects.create(school=school, family_name=family_name)


def _make_student(school, family, *, first_name="Jane", last_name="Doe", number="S001"):
    return Student.objects.create(
        school=school,
        family=family,
        student_number=number,
        first_name=first_name,
        last_name=last_name,
        dob=date(2012, 3, 15),
    )


def _make_staff_user(school, suffix=""):
    user = UserAccount.objects.create_user(
        username=f"staff{suffix}",
        password="pass",
        email=f"staff{suffix}@test.example.com",
        is_staff=True,
        school=school,
    )
    UserRole.objects.get_or_create(user=user, school=school, role_code="AID_DIRECTOR")
    for code in ("financial_aid.view", "financial_aid.edit"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=permission)
    return user


def _make_application(school, ay, family):
    return AidApplication.objects.create(
        school=school,
        academic_year=ay,
        family=family,
        status=AidApplication.STATUS_SUBMITTED,
        household_size=4,
        income_annual_cents=60_000_00,
    )


def _make_policy(school, ay):
    return AidPolicy.objects.create(
        school=school,
        academic_year=ay,
        max_award_percent=60,
        min_award_percent=0,
        need_income_floor_cents=0,
    )


def _make_budget(school, ay, bucket=AidAward.TYPE_NEED, allocated=5_000_000, awarded=0):
    return AidBudgetTracker.objects.create(
        school=school,
        academic_year=ay,
        bucket=bucket,
        allocated_cents=allocated,
        awarded_cents=awarded,
    )


def _make_award(school, ay, student, *, awarded_cents=50_000, bucket=AidAward.TYPE_NEED):
    return AidAward.objects.create(
        school=school,
        academic_year=ay,
        student=student,
        award_type=bucket,
        awarded_cents=awarded_cents,
        decision_status=AidAward.DECISION_OFFERED,
    )


def _make_chart_account(school):
    return ChartAccount.objects.create(
        school=school, code="AID", name="Financial Aid", account_type="INCOME"
    )


def _json_post(client, url, data, school):
    return client.post(
        url,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_X_SCHOOL_ID=str(school.id),
    )


# ===========================================================================
# 1. admin_aid_overview
# ===========================================================================

class TestAdminAidOverview(TestCase):
    def setUp(self):
        self.school = _make_school("Overview School")
        self.ay = _make_ay(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.user = _make_staff_user(self.school, "ov")
        _make_application(self.school, self.ay, self.family)
        _make_award(self.school, self.ay, self.student)
        _make_budget(self.school, self.ay)
        self.url = f"/api/aid/admin/overview/"
        self.client.force_login(self.user)

    def test_returns_200_with_expected_shape(self):
        r = self.client.get(
            self.url,
            {"academic_year_id": str(self.ay.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("applications", data)
        self.assertIn("awards", data)
        self.assertIn("budgets", data)
        self.assertIsInstance(data["applications"], list)
        self.assertIsInstance(data["awards"], list)
        self.assertIsInstance(data["budgets"], list)

    def test_correct_counts_returned(self):
        r = self.client.get(
            self.url,
            {"academic_year_id": str(self.ay.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        data = r.json()
        self.assertEqual(len(data["applications"]), 1)
        self.assertEqual(len(data["awards"]), 1)
        self.assertEqual(len(data["budgets"]), 1)

    def test_missing_school_header_uses_authenticated_school(self):
        """A user with one direct school may use authenticated tenant fallback."""
        r = self.client.get(self.url, {"academic_year_id": str(self.ay.id)})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data["applications"]), 1)
        self.assertEqual(len(data["awards"]), 1)
        self.assertEqual(len(data["budgets"]), 1)

    def test_missing_academic_year_id_returns_400(self):
        r = self.client.get(self.url, HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(r.status_code, 400)

    def test_unauthenticated_returns_403(self):
        self.client.logout()
        r = self.client.get(
            self.url,
            {"academic_year_id": str(self.ay.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertIn(r.status_code, (401, 403))

    def test_tenant_isolation_different_school_data_not_returned(self):
        other_school = _make_school("Other School")
        other_ay = _make_ay(other_school, "2026-27")
        other_family = _make_family(other_school, "Smith")
        other_student = _make_student(other_school, other_family, number="S999")
        _make_application(other_school, other_ay, other_family)
        _make_award(other_school, other_ay, other_student)

        # Request with our school's ID should not return other school's data
        r = self.client.get(
            self.url,
            {"academic_year_id": str(self.ay.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        data = r.json()
        self.assertEqual(len(data["applications"]), 1)
        self.assertEqual(len(data["awards"]), 1)


# ===========================================================================
# 2. admin_recommend_award
# ===========================================================================

class TestAdminRecommendAward(TestCase):
    def setUp(self):
        self.school = _make_school("Recommend School")
        self.ay = _make_ay(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.user = _make_staff_user(self.school, "rec")
        self.app = _make_application(self.school, self.ay, self.family)
        self.app.income_annual_cents = 40_000_00
        self.app.save()
        self.policy = _make_policy(self.school, self.ay)
        self.url = "/api/aid/admin/recommend-award/"
        self.client.force_login(self.user)

    def test_success_returns_201_with_award_and_explanation(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(r.status_code, 201)
        data = r.json()
        self.assertIn("award", data)
        self.assertIn("explanation", data)
        # Verify award was persisted
        self.assertTrue(AidAward.objects.filter(pk=data["award"]["id"]).exists())

    def test_created_award_stores_engine_outputs(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        award_data = r.json()["award"]
        self.assertIsNotNone(award_data.get("mas_score"))
        self.assertIn("mas_modifier_bps", award_data)

    def test_second_child_is_explicit_award_recipient(self):
        other = _make_student(self.school, self.family, first_name="Blair", number="S002")
        response = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(other.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(response.status_code, 201, response.content)
        award = AidAward.objects.get(pk=response.json()["award"]["id"])
        self.assertEqual(award.student_id, other.id)

    def test_student_from_another_family_is_not_awarded(self):
        unrelated_family = _make_family(self.school, "Unrelated")
        unrelated = _make_student(self.school, unrelated_family, number="S003")
        response = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(unrelated.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(AidAward.objects.filter(student=unrelated).exists())

    def test_student_from_another_school_is_not_awarded(self):
        foreign_school = _make_school("Foreign School")
        foreign_family = _make_family(foreign_school)
        foreign = _make_student(foreign_school, foreign_family, number="S001")
        response = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(foreign.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(AidAward.objects.filter(student=foreign).exists())

    def test_missing_student_id_is_rejected(self):
        response = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AidAward.objects.filter(aid_application=self.app).exists())

    def test_malformed_student_id_is_rejected(self):
        response = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": "not-a-uuid",
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AidAward.objects.filter(aid_application=self.app).exists())

    def test_invalid_award_bucket_is_rejected(self):
        response = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            "bucket": "INVALID",
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AidAward.objects.filter(aid_application=self.app).exists())

    def test_non_string_award_bucket_returns_400(self):
        for invalid_bucket in (["NEED"], {"value": "NEED"}):
            with self.subTest(bucket=repr(invalid_bucket)):
                response = _json_post(self.client, self.url, {
                    "application_id": str(self.app.id),
                    "student_id": str(self.student.id),
                    "bucket": invalid_bucket,
                    "gross_tuition_cents": 10_000_00,
                }, self.school)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertFalse(AidAward.objects.filter(aid_application=self.app).exists())

    def test_rejected_recommendations_leave_financial_records_unchanged(self):
        """Invalid students/buckets must not change awards, budgets, ledger or audits."""
        from aid.models import AidAuditEvent, AidFinancialProfile
        from core.models import LedgerEntry
        from ledger.models import Credit, Payment

        _make_award(self.school, self.ay, self.student)
        _make_budget(self.school, self.ay)
        wrong_family = _make_family(self.school, "Other Family")
        wrong_student = _make_student(self.school, wrong_family, number="REJ-2")
        foreign_school = _make_school("Other Tenant")
        foreign_family = _make_family(foreign_school)
        foreign_student = _make_student(foreign_school, foreign_family, number="REJ-3")
        foreign_app = _make_application(foreign_school, _make_ay(foreign_school), foreign_family)

        financial_models = (
            AidApplication, AidAward, AidBudgetTracker, AidPolicy, AidFinancialProfile,
            AidAuditEvent, LedgerEntry, Credit, Payment, ChartAccount,
        )

        def financial_state():
            return {m._meta.label: list(m.objects.order_by("pk").values()) for m in financial_models}

        baseline = financial_state()
        valid = {
            "application_id": self.app.id,
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }
        cases = (
            ("missing student", {"student_id": None}, 400),
            ("malformed UUID", {"student_id": "not-a-uuid"}, 400),
            ("wrong family", {"student_id": str(wrong_student.id)}, 404),
            ("other school student", {"student_id": str(foreign_student.id)}, 404),
            ("other school application", {"application_id": foreign_app.id}, 404),
            ("bad bucket", {"bucket": "INVALID"}, 400),
            ("non-string bucket", {"bucket": ["NEED"]}, 400),
        )
        for label, override, status_code in cases:
            with self.subTest(case=label):
                response = _json_post(self.client, self.url, {**valid, **override}, self.school)
                self.assertEqual(response.status_code, status_code, response.content)
                self.assertEqual(financial_state(), baseline)

    def test_missing_policy_returns_404(self):
        # No policy for this school/year → 404
        AidPolicy.objects.filter(school=self.school, academic_year=self.ay).delete()
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(r.status_code, 404)

    def test_missing_application_returns_404(self):
        r = _json_post(self.client, self.url, {
            "application_id": 999999999,  # integer PK (AidApplication auto-pk)
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(r.status_code, 404)

    def test_missing_required_fields_returns_400(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            # missing bucket and gross_tuition_cents
        }, self.school)
        self.assertEqual(r.status_code, 400)

    def test_zero_tuition_returns_400(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 0,
        }, self.school)
        self.assertEqual(r.status_code, 400)

    def test_unauthenticated_returns_403(self):
        self.client.logout()
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "student_id": str(self.student.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertIn(r.status_code, (401, 403))


# ===========================================================================
# 3. admin_approve_award
# ===========================================================================

class TestAdminApproveAward(TestCase):
    def setUp(self):
        self.school = _make_school("Approve School")
        self.ay = _make_ay(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.user = _make_staff_user(self.school, "app")
        self.award = _make_award(self.school, self.ay, self.student, awarded_cents=50_000)
        self.budget = _make_budget(self.school, self.ay, allocated=5_000_000, awarded=0)
        _make_chart_account(self.school)
        self.url = f"/api/aid/admin/awards/{self.award.id}/approve/"
        self.client.force_login(self.user)

    def test_success_returns_200(self):
        r = _json_post(self.client, self.url, {"reason": "Approved in test"}, self.school)
        self.assertEqual(r.status_code, 200)
        self.award.refresh_from_db()
        self.assertEqual(self.award.decision_status, AidAward.DECISION_ACCEPTED)

    def test_budget_decremented_after_approval(self):
        _json_post(self.client, self.url, {"reason": "Budget test"}, self.school)
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.awarded_cents, 50_000)

    def test_idempotent_second_call_returns_200(self):
        _json_post(self.client, self.url, {"reason": "First"}, self.school)
        before = self._financial_state()
        r = _json_post(self.client, self.url, {"reason": "Second"}, self.school)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self._financial_state(), before)
        # Budget should NOT be double-decremented
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.awarded_cents, 50_000)

    @staticmethod
    def _financial_state():
        from aid.models import AidAuditEvent
        from core.models import LedgerEntry
        from ledger.models import Credit, LedgerAccount, Payment

        models = (
            AidAward, AidBudgetTracker, AidAuditEvent, LedgerEntry,
            LedgerAccount, Credit, Payment, ChartAccount,
        )
        return {
            model._meta.label: list(model.objects.order_by("pk").values())
            for model in models
        }

    def test_accepted_retry_changed_student_returns_409_without_writes(self):
        first = _json_post(self.client, self.url, {"reason": "Initial"}, self.school)
        self.assertEqual(first.status_code, 200, first.content)
        second_student = _make_student(
            self.school, self.family, first_name="Second", number="S002",
        )
        AidAward.objects.filter(pk=self.award.pk).update(student=second_student)
        before = self._financial_state()

        response = _json_post(self.client, self.url, {"reason": "Unsafe replay"}, self.school)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(
            response.json()["error"], "Award posting requires controlled reconciliation.",
        )
        self.assertEqual(self._financial_state(), before)

    def test_accepted_retry_changed_year_returns_409_without_writes(self):
        first = _json_post(self.client, self.url, {"reason": "Initial"}, self.school)
        self.assertEqual(first.status_code, 200, first.content)
        next_year = AcademicYear.objects.create(
            school=self.school, name="2027-28",
            start_date=date(2027, 8, 1), end_date=date(2028, 5, 31),
        )
        AidAward.objects.filter(pk=self.award.pk).update(academic_year=next_year)
        before = self._financial_state()

        response = _json_post(self.client, self.url, {"reason": "Unsafe replay"}, self.school)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(
            response.json()["error"], "Award posting requires controlled reconciliation.",
        )
        self.assertEqual(self._financial_state(), before)



    def test_unrelated_service_validation_error_is_not_masked_as_financial_409(self):
        from unittest.mock import patch
        from django.core.exceptions import ValidationError

        before = self._financial_state()
        # Django TestClient re-raises unhandled view errors by default. Verify
        # the actual generic HTTP response instead of raising in the harness.
        self.client.raise_request_exception = False
        with patch("aid.api_views.approve_award", side_effect=ValidationError("Unrelated synthetic validation")):
            response = _json_post(self.client, self.url, {"reason": "Internal failure"}, self.school)
        self.assertEqual(response.status_code, 500, response.content)
        self.assertNotEqual(response.status_code, 409)
        self.assertEqual(self._financial_state(), before)

    def test_invalid_json_returns_400_without_financial_writes(self):
        before = self._financial_state()
        response = self.client.post(
            self.url, data='{"reason":', content_type="application/json",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(response.status_code, 400, response.content)
        self.assertEqual(self._financial_state(), before)


    def test_non_object_json_returns_400_without_financial_writes(self):
        before = self._financial_state()
        for payload in ("[]", "null", '"reason"'):
            with self.subTest(payload=payload):
                response = self.client.post(
                    self.url, data=payload, content_type="application/json",
                    HTTP_X_SCHOOL_ID=str(self.school.id),
                )
                self.assertEqual(response.status_code, 400, response.content)
                self.assertEqual(self._financial_state(), before)

    def test_invalid_reason_type_returns_400_without_financial_writes(self):
        before = self._financial_state()
        for reason in (None, [], {"nested": "no"}):
            with self.subTest(reason=repr(reason)):
                response = _json_post(self.client, self.url, {"reason": reason}, self.school)
                self.assertEqual(response.status_code, 400, response.content)
                self.assertEqual(self._financial_state(), before)

    def test_foreign_tenant_award_is_404_without_financial_writes(self):
        other_school = _make_school("Other approval tenant")
        other_year = _make_ay(other_school)
        other_family = _make_family(other_school)
        other_student = _make_student(other_school, other_family)
        other_award = _make_award(other_school, other_year, other_student)
        before = self._financial_state()
        response = _json_post(
            self.client, f"/api/aid/admin/awards/{other_award.pk}/approve/",
            {"reason": "Not our award"}, self.school,
        )
        self.assertEqual(response.status_code, 404, response.content)
        self.assertEqual(self._financial_state(), before)

    def test_unprivileged_replay_is_403_without_financial_writes(self):
        first = _json_post(self.client, self.url, {"reason": "Initial"}, self.school)
        self.assertEqual(first.status_code, 200, first.content)
        other_student = _make_student(
            self.school, self.family, first_name="Second", number="S002",
        )
        AidAward.objects.filter(pk=self.award.pk).update(student=other_student)
        unprivileged = UserAccount.objects.create_user(
            username="unprivileged-approval",
            password="test-only",
            school=self.school,
            is_staff=True,
        )
        self.client.force_login(unprivileged)
        before = self._financial_state()
        response = _json_post(self.client, self.url, {"reason": "Unprivileged replay"}, self.school)
        self.assertEqual(response.status_code, 403, response.content)
        self.assertEqual(self._financial_state(), before)

    def test_declined_award_is_controlled_conflict_without_financial_writes(self):
        AidAward.objects.filter(pk=self.award.pk).update(
            decision_status=AidAward.DECISION_DECLINED,
        )
        before = self._financial_state()
        response = _json_post(self.client, self.url, {"reason": "Unsafe reinstatement"}, self.school)
        self.assertEqual(response.status_code, 409, response.content)
        self.assertEqual(
            response.json()["error"], "Award posting requires controlled reconciliation.",
        )
        self.assertEqual(self._financial_state(), before)

    def test_budget_overrun_returns_409(self):
        # Award amount exceeds remaining budget
        overrun_award = _make_award(self.school, self.ay, self.student, awarded_cents=999_999_999)
        url = f"/api/aid/admin/awards/{overrun_award.id}/approve/"
        r = _json_post(self.client, url, {"reason": "Should fail"}, self.school)
        self.assertEqual(r.status_code, 409)

    def test_no_budget_tracker_returns_409(self):
        # Remove the budget row
        self.budget.delete()
        r = _json_post(self.client, self.url, {"reason": "No budget"}, self.school)
        self.assertEqual(r.status_code, 409)

    def test_award_not_found_returns_404(self):
        url = "/api/aid/admin/awards/99999999/approve/"
        r = _json_post(self.client, url, {"reason": "Missing"}, self.school)
        self.assertEqual(r.status_code, 404)

    def test_unauthenticated_returns_403(self):
        self.client.logout()
        r = _json_post(self.client, self.url, {"reason": "Unauth"}, self.school)
        self.assertIn(r.status_code, (401, 403))


# ===========================================================================
# 4. family_aid_status
# ===========================================================================

class TestFamilyAidStatus(TestCase):
    def setUp(self):
        self.school = _make_school("Family School")
        self.ay = _make_ay(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.user = _make_staff_user(self.school, "fam")
        self.app = _make_application(self.school, self.ay, self.family)
        self.award = _make_award(self.school, self.ay, self.student)
        self.url = "/api/aid/family/status/"
        self.client.force_login(self.user)

    def _get(self, **kwargs):
        return self.client.get(
            self.url,
            kwargs,
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )

    def test_success_returns_200_with_application_and_awards(self):
        r = self._get(student_id=str(self.student.id), academic_year_id=str(self.ay.id))
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIsNotNone(data["application"])
        self.assertEqual(len(data["awards"]), 1)

    def test_no_application_returns_null(self):
        # Different year, no application
        ay2 = AcademicYear.objects.create(
            school=self.school, name="2027-28",
            start_date=date(2027, 8, 1), end_date=date(2028, 5, 31),
        )
        r = self._get(student_id=str(self.student.id), academic_year_id=str(ay2.id))
        self.assertEqual(r.status_code, 200)
        self.assertIsNone(r.json()["application"])

    def test_missing_student_id_returns_400(self):
        r = self.client.get(
            self.url,
            {"academic_year_id": str(self.ay.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_missing_academic_year_id_returns_400(self):
        r = self.client.get(
            self.url,
            {"student_id": str(self.student.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 400)

    def test_student_from_different_school_returns_404(self):
        other_school = _make_school("Foreign School")
        other_ay = _make_ay(other_school)
        other_family = _make_family(other_school, "Jones")
        other_student = _make_student(other_school, other_family, number="X001")
        # Request using current school's header but other school's student
        r = self.client.get(
            self.url,
            {"student_id": str(other_student.id), "academic_year_id": str(self.ay.id)},
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        self.assertEqual(r.status_code, 404)

    def test_unauthenticated_returns_403(self):
        self.client.logout()
        r = self._get(student_id=str(self.student.id), academic_year_id=str(self.ay.id))
        self.assertIn(r.status_code, (401, 403))
