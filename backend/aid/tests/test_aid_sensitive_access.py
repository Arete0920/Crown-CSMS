"""Fail-closed financial-aid admin and family access regression tests."""
from datetime import date
from uuid import uuid4

from django.test import TestCase
from rest_framework.test import APIClient

from aid.models import AidApplication, AidAward, AidBudgetTracker, AidFinancialProfile
from core.models import (
    AcademicYear, CrownPermission, Family, Guardian, RolePermission,
    School, Student, UserAccount, UserRole,
)


class AidSensitiveAccessTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic Aid Access School")
        self.other_school = School.objects.create(name="Synthetic Foreign Aid School")
        self.year = AcademicYear.objects.create(
            school=self.school, name="2026-2027",
            start_date=date(2026, 8, 1), end_date=date(2027, 5, 31),
        )
        self.family = Family.objects.create(school=self.school, family_name="Access One")
        self.other_family = Family.objects.create(school=self.school, family_name="Access Two")
        self.student = Student.objects.create(
            school=self.school, family=self.family, student_number="AID-1",
            first_name="A", last_name="Student", dob=date(2013, 1, 1),
        )
        self.other_student = Student.objects.create(
            school=self.school, family=self.other_family, student_number="AID-2",
            first_name="B", last_name="Student", dob=date(2013, 1, 1),
        )
        self.application = AidApplication.objects.create(
            school=self.school, academic_year=self.year, family=self.family,
            status=AidApplication.STATUS_SUBMITTED,
        )
        self.award = AidAward.objects.create(
            school=self.school, academic_year=self.year, student=self.student,
            awarded_cents=50000, decision_status=AidAward.DECISION_OFFERED,
        )
        self.client = APIClient()
        self.staff = UserAccount.objects.create_user(
            username="ungranted-aid-staff", password="test-only",
            school=self.school, is_staff=True,
        )
        self.client.force_authenticate(user=self.staff)

    def _get(self, path, params=None, *, school=None):
        return self.client.get(
            path, params or {}, HTTP_X_SCHOOL_ID=str((school or self.school).id),
        )

    def _post(self, path, data):
        return self.client.post(
            path, data, format="json", HTTP_X_SCHOOL_ID=str(self.school.id),
        )

    def _grant(self, *, edit=False):
        UserRole.objects.get_or_create(
            user=self.staff, school=self.school, role_code="AID_DIRECTOR",
        )
        codes = ("financial_aid.view", "financial_aid.edit") if edit else ("financial_aid.view",)
        for code in codes:
            permission, _ = CrownPermission.objects.get_or_create(code=code)
            RolePermission.objects.get_or_create(
                role_code="AID_DIRECTOR", permission=permission,
            )

    def test_ungranted_staff_cannot_read_admin_records(self):
        for path, params in (
            ("/api/aid/admin/overview/", {"academic_year_id": str(self.year.id)}),
            (f"/api/aid/admin/applications/{self.application.id}/review/", None),
        ):
            with self.subTest(path=path):
                self.assertEqual(self._get(path, params).status_code, 403)

    def test_ungranted_staff_cannot_change_award_or_profile(self):
        profile = AidFinancialProfile.objects.create(
            school=self.school, academic_year=self.year,
            family=self.family, consent_to_reuse=True,
        )
        award_count = AidAward.objects.count()
        profile_count = AidFinancialProfile.objects.count()
        budget_count = AidBudgetTracker.objects.count()
        requests = (
            ("/api/aid/admin/recommend-award/", {
                "application_id": self.application.id,
                "bucket": "NEED", "gross_tuition_cents": 100000,
            }),
            (f"/api/aid/admin/awards/{self.award.id}/approve/", {"reason": "ungranted"}),
            ("/api/aid/admin/financial-profiles/carry-forward/", {
                "source_profile_id": profile.id,
                "academic_year_id": self.year.id,
            }),
        )
        for path, payload in requests:
            with self.subTest(path=path):
                self.assertEqual(self._post(path, payload).status_code, 403)
        self.award.refresh_from_db()
        self.assertEqual(self.award.decision_status, AidAward.DECISION_OFFERED)
        self.assertIsNone(self.award.ledger_entry_id)
        self.assertEqual(AidAward.objects.count(), award_count)
        self.assertEqual(AidFinancialProfile.objects.count(), profile_count)
        self.assertEqual(AidBudgetTracker.objects.count(), budget_count)

    def test_read_grant_does_not_grant_write(self):
        self._grant()
        response = self._get(
            "/api/aid/admin/overview/", {"academic_year_id": str(self.year.id)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["applications"]), 1)
        self.assertEqual(
            self._get(f"/api/aid/admin/applications/{self.application.id}/review/").status_code,
            200,
        )
        self.assertEqual(
            self._post(f"/api/aid/admin/awards/{self.award.id}/approve/", {}).status_code,
            403,
        )
        self.award.refresh_from_db()
        self.assertEqual(self.award.decision_status, AidAward.DECISION_OFFERED)

    def test_parent_requires_verified_guardian_link_for_own_family(self):
        guardian = Guardian.objects.create(
            school=self.school, family=self.family, first_name="Parent",
            last_name="One", email="parent-one@example.invalid", relationship="MOTHER",
        )
        parent = UserAccount.objects.create_user(
            username="parent-identity-test", password="test-only",
            email=guardian.email, school=self.school,
        )
        UserRole.objects.create(user=parent, school=self.school, role_code="PARENT")
        self.client.force_authenticate(user=parent)
        params = {"student_id": str(self.student.id), "academic_year_id": str(self.year.id)}
        # An email match without a linked guardian identity proves nothing.
        self.assertEqual(self._get("/api/aid/family/status/", params).status_code, 404)
        parent.guardian = guardian
        parent.save(update_fields=["guardian"])
        response = self._get("/api/aid/family/status/", params)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json()["application"])
        self.assertEqual(len(response.json()["awards"]), 1)
        params["student_id"] = str(self.other_student.id)
        self.assertEqual(self._get("/api/aid/family/status/", params).status_code, 404)

    def test_foreign_guardian_link_cannot_grant_family_aid(self):
        foreign_family = Family.objects.create(
            school=self.other_school, family_name="Foreign Guardian",
        )
        foreign_guardian = Guardian.objects.create(
            school=self.other_school, family=foreign_family,
            first_name="Foreign", last_name="Parent",
            email="foreign@example.invalid", relationship="OTHER",
        )
        parent = UserAccount.objects.create_user(
            username="mismatched-parent-link", password="test-only",
            email="foreign-linked-parent@example.invalid",
            school=self.school, guardian=foreign_guardian,
        )
        UserRole.objects.create(user=parent, school=self.school, role_code="PARENT")
        self.client.force_authenticate(user=parent)
        self.assertEqual(
            self._get("/api/aid/family/status/", {
                "student_id": str(self.student.id),
                "academic_year_id": str(self.year.id),
            }).status_code, 404,
        )

    def test_aid_officer_can_view_family_status_with_view_grant(self):
        self._grant()
        response = self._get("/api/aid/family/status/", {
            "student_id": str(self.student.id),
            "academic_year_id": str(self.year.id),
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["awards"]), 1)
    def test_family_status_invalid_student_or_year_uuid_denied_without_error(self):
        self._grant()
        base = {
            "student_id": str(self.student.id),
            "academic_year_id": str(self.year.id),
        }
        for field in ("student_id", "academic_year_id"):
            with self.subTest(field=field):
                params = dict(base)
                params[field] = "not-a-uuid"
                response = self._get("/api/aid/family/status/", params)
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("awards", response.json())

    def test_aid_reader_denied_when_student_family_belongs_to_other_school(self):
        self._grant()
        foreign_family = Family.objects.create(
            school=self.other_school, family_name="Foreign Linked Family",
        )
        Student.objects.filter(pk=self.student.pk).update(family=foreign_family)
        response = self._get("/api/aid/family/status/", {
            "student_id": str(self.student.id),
            "academic_year_id": str(self.year.id),
        })
        self.assertEqual(response.status_code, 404)
        self.assertNotIn("awards", response.json())

    def test_family_denials_do_not_reveal_student_existence(self):
        responses = [self._get("/api/aid/family/status/", {
            "student_id": str(student_id), "academic_year_id": str(self.year.id),
        }) for student_id in (self.other_student.id, uuid4())]
        self.assertEqual([response.status_code for response in responses], [404, 404])
        self.assertEqual(responses[0].json(), responses[1].json())
