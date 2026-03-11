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
from core.models import AcademicYear, Family, School, Student, UserAccount
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


def _make_staff_user(suffix=""):
    """Staff user with school=None; bypasses cross-tenant check."""
    return UserAccount.objects.create_user(
        username=f"staff{suffix}",
        password="pass",
        email=f"staff{suffix}@test.example.com",
        is_staff=True,
    )


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
        self.user = _make_staff_user("ov")
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

    def test_missing_school_header_returns_400(self):
        r = self.client.get(self.url, {"academic_year_id": str(self.ay.id)})
        self.assertIn(r.status_code, (400, 403))

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
        self.user = _make_staff_user("rec")
        self.app = _make_application(self.school, self.ay, self.family)
        self.app.income_annual_cents = 40_000_00
        self.app.save()
        self.policy = _make_policy(self.school, self.ay)
        self.url = "/api/aid/admin/recommend-award/"
        self.client.force_login(self.user)

    def test_success_returns_201_with_award_and_explanation(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
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
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        award_data = r.json()["award"]
        self.assertIsNotNone(award_data.get("mas_score"))
        self.assertIn("mas_modifier_bps", award_data)

    def test_missing_policy_returns_404(self):
        # No policy for this school/year → 404
        AidPolicy.objects.filter(school=self.school, academic_year=self.ay).delete()
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(r.status_code, 404)

    def test_missing_application_returns_404(self):
        r = _json_post(self.client, self.url, {
            "application_id": 999999999,  # integer PK (AidApplication auto-pk)
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 10_000_00,
        }, self.school)
        self.assertEqual(r.status_code, 404)

    def test_missing_required_fields_returns_400(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            # missing bucket and gross_tuition_cents
        }, self.school)
        self.assertEqual(r.status_code, 400)

    def test_zero_tuition_returns_400(self):
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
            "bucket": AidAward.TYPE_NEED,
            "gross_tuition_cents": 0,
        }, self.school)
        self.assertEqual(r.status_code, 400)

    def test_unauthenticated_returns_403(self):
        self.client.logout()
        r = _json_post(self.client, self.url, {
            "application_id": str(self.app.id),
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
        self.user = _make_staff_user("app")
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
        r = _json_post(self.client, self.url, {"reason": "Second"}, self.school)
        self.assertEqual(r.status_code, 200)
        # Budget should NOT be double-decremented
        self.budget.refresh_from_db()
        self.assertEqual(self.budget.awarded_cents, 50_000)

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
        self.user = _make_staff_user("fam")
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
