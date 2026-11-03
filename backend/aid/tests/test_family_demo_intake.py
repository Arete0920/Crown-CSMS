"""Regression contract for the local-only fictional school Jireh parent workflow."""
from datetime import date
from unittest import skipUnless
from unittest.mock import patch

from django.conf import settings
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from aid.models import (
    AidApplication, AidAuditEvent, AidAward, AidFinancialLineItem,
    AidFinancialProfile, AidHouseholdMember,
)
from core.models import (
    AcademicYear, CrownPermission, Family, Guardian, RolePermission,
    School, Student, UserAccount, UserRole,
)

URL = "/api/v1/aid/family/demo-intake/"


@skipUnless(
    settings.DATABASES["default"]["ENGINE"].endswith(".sqlite3"),
    "Local-only fictional aid intake requires SQLite; run dedicated sandbox acceptance.",
)
@override_settings(
    DEBUG=True,
    CROWN_ENV="local",
    CROWN_SANDBOX_ALLOW_OPEN_SESSION=True,
    CROWN_DEMO_MODE=False,
)
class FictionalFamilyAidIntakeTests(TestCase):
    def setUp(self):
        # Disposable Django SQLite test database substitutes for the exact
        # Heritage path only within this test harness. The endpoint itself
        # enforces the real canonical file path in normal operation.
        guard = patch("aid.family_demo_intake._require_isolated_local_database")
        guard.start()
        self.addCleanup(guard.stop)
        self.schools = [
            School.objects.create(name="Fictional School " + str(index))
            for index in (1, 2)
        ]
        self.parents = []
        self.students = []
        self.years = []
        self.families = []

        for index, school in enumerate(self.schools):
            year = AcademicYear.objects.create(
                school=school,
                name="2026-2027",
                start_date=date(2026, 8, 1),
                end_date=date(2027, 6, 1),
                is_current=True,
            )
            family = Family.objects.create(
                school=school, family_name="Fictional Household " + str(index)
            )
            guardian = Guardian.objects.create(
                school=school,
                family=family,
                first_name="Example",
                last_name="Guardian",
                email="guardian%d@example.invalid" % index,
                relationship="MOTHER",
                portal_access=True,
            )
            parent = UserAccount.objects.create_user(
                username="fictional-parent-%d" % index,
                password="test-only",
                school=school,
                guardian=guardian,
                email=guardian.email,
            )
            UserRole.objects.create(user=parent, school=school, role_code="PARENT")
            student = Student.objects.create(
                school=school,
                family=family,
                student_number="FICTIONAL-%d" % index,
                first_name="Example",
                last_name="Student",
                dob=date(2014, 3, 1),
                status="ACTIVE",
            )
            self.parents.append(parent)
            self.students.append(student)
            self.years.append(year)
            self.families.append(family)

    def client_for(self, user, school=None):
        client = APIClient()
        client.force_authenticate(user=user)
        return client, {"HTTP_X_SCHOOL_ID": str((school or user.school).id)}

    def payload(self, index=0):
        return {
            "academic_year_id": str(self.years[index].pk),
            "student_ids": [str(self.students[index].pk)],
            "household_size": 3,
            "scenario": "fictional_modest",
            "fictional_acknowledged": True,
        }

    def submit(self, index=0, payload=None, user=None, school=None):
        client, headers = self.client_for(user or self.parents[index], school)
        return client.post(URL, payload if payload is not None else self.payload(index), format="json", **headers)

    def get_state(self, index=0, user=None, school=None):
        client, headers = self.client_for(user or self.parents[index], school)
        return client.get(URL, **headers)

    def test_fictional_submission_persists_canonical_application_profile_students_and_audit(self):
        response = self.submit()
        self.assertEqual(response.status_code, 201, response.content)
        app = AidApplication.objects.get(pk=response.json()["application"]["id"])
        self.assertEqual(app.school, self.schools[0])
        self.assertEqual(app.family, self.families[0])
        self.assertEqual(app.academic_year, self.years[0])
        self.assertEqual(app.status, AidApplication.STATUS_SUBMITTED)
        self.assertIsNotNone(app.submitted_at)
        self.assertIsNotNone(app.financial_profile_id)
        self.assertEqual(app.financial_profile.verification_status, AidFinancialProfile.STATUS_DRAFT)
        self.assertFalse(app.financial_profile.consent_to_reuse)
        self.assertEqual(app.financial_profile.line_items.count(), 3)
        self.assertFalse(app.financial_profile.line_items.filter(verified=True).exists())
        self.assertEqual(
            app.financial_profile.household_members.get(role=AidHouseholdMember.ROLE_STUDENT).student_id,
            self.students[0].id,
        )
        self.assertTrue(AidAuditEvent.objects.filter(
            school=self.schools[0], entity_type=AidAuditEvent.ENTITY_APPLICATION,
            entity_id=str(app.pk), action="STATUS_SUBMITTED",
        ).exists())
        # Fresh authenticated client models a page reload or renewed session.
        state = self.get_state()
        self.assertEqual(state.status_code, 200)
        self.assertEqual(str(state.json()["applications"][0]["id"]), str(app.id))
        self.assertEqual(state.json()["applications"][0]["status"], AidApplication.STATUS_SUBMITTED)
        self.assertEqual(state.json()["applications"][0]["student_ids"], [str(self.students[0].pk)])
        self.assertNotIn("income_annual_cents", state.json()["applications"][0])
        self.assertNotIn("financial_profile", state.json()["applications"][0])

    def test_two_unrelated_schools_have_separate_records_and_readback(self):
        first = self.submit(0)
        second = self.submit(1)
        self.assertEqual(first.status_code, 201, first.content)
        self.assertEqual(second.status_code, 201, second.content)
        first_id = first.json()["application"]["id"]
        second_id = second.json()["application"]["id"]
        self.assertNotEqual(first_id, second_id)
        self.assertEqual([str(item["id"]) for item in self.get_state(0).json()["applications"]], [str(first_id)])
        self.assertEqual([str(item["id"]) for item in self.get_state(1).json()["applications"]], [str(second_id)])
        self.assertEqual(AidApplication.objects.count(), 2)

    def test_duplicate_requests_and_session_changes_do_not_duplicate(self):
        self.assertEqual(self.submit().status_code, 201)
        self.assertEqual(self.submit().status_code, 409)
        client, headers = self.client_for(self.parents[0])
        self.assertEqual(client.post(URL, self.payload(), format="json", **headers).status_code, 409)
        self.assertEqual(AidApplication.objects.count(), 1)
        self.assertEqual(AidFinancialProfile.objects.count(), 1)

    def test_validation_failures_do_not_write(self):
        invalid = (
            {"fictional_acknowledged": False},
            {"scenario": "actual_income"},
            {"scenario": {"injected": "object"}},
            {"household_size": -2},
            {"household_size": True},
            {"student_ids": []},
            {"student_ids": ["not-a-uuid"]},
            {"student_ids": [str(self.students[0].pk)] * 2},
            {"academic_year_id": "garbage"},
            {"raw_income": "9999"},
            {"household_income": 9000},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                payload = {**self.payload(), **changes}
                response = self.submit(payload=payload)
                self.assertIn(response.status_code, (400, 404), response.content)
        self.assertEqual(AidApplication.objects.count(), 0)
        self.assertEqual(AidFinancialProfile.objects.count(), 0)
        self.assertEqual(AidFinancialLineItem.objects.count(), 0)

    def test_rejects_foreign_student_same_school_other_family_and_inconsistent_year(self):
        wrong = self.payload()
        wrong["student_ids"] = [str(self.students[1].id)]
        self.assertEqual(self.submit(payload=wrong).status_code, 404)
        another_family = Family.objects.create(school=self.schools[0], family_name="Unrelated")
        unrelated = Student.objects.create(
            school=self.schools[0], family=another_family, student_number="UNRELATED",
            first_name="Other", last_name="Student", dob=date(2015, 1, 1),
        )
        wrong["student_ids"] = [str(unrelated.pk)]
        self.assertEqual(self.submit(payload=wrong).status_code, 404)
        wrong = self.payload()
        wrong["academic_year_id"] = str(self.years[1].pk)
        self.assertEqual(self.submit(payload=wrong).status_code, 404)
        self.assertEqual(AidApplication.objects.count(), 0)

    def test_wrong_tenant_header_does_not_expose_or_write(self):
        self.assertIn(self.get_state(0, school=self.schools[1]).status_code, (403, 404))
        self.assertIn(self.submit(0, school=self.schools[1]).status_code, (403, 404))
        self.assertEqual(AidApplication.objects.count(), 0)

    def test_unlinked_guardian_teacher_and_other_user_denied(self):
        teacher = UserAccount.objects.create_user(
            username="fictional-teacher", email="fictional-teacher@example.invalid", password="test-only", school=self.schools[0]
        )
        UserRole.objects.create(user=teacher, school=self.schools[0], role_code="TEACHER")
        unlinked = UserAccount.objects.create_user(
            username="fictional-unlinked", email="fictional-unlinked@example.invalid", password="test-only", school=self.schools[0]
        )
        UserRole.objects.create(user=unlinked, school=self.schools[0], role_code="PARENT")
        for user in (teacher, unlinked):
            with self.subTest(username=user.username):
                self.assertEqual(self.get_state(user=user).status_code, 404)
                self.assertEqual(self.submit(user=user).status_code, 404)
        client = APIClient()
        self.assertIn(client.get(URL, HTTP_X_SCHOOL_ID=str(self.schools[0].pk)).status_code, (401, 403))
        self.assertIn(client.post(URL, self.payload(), format="json", HTTP_X_SCHOOL_ID=str(self.schools[0].pk)).status_code, (401, 403))
        self.assertEqual(AidApplication.objects.count(), 0)


    def test_non_heritage_sqlite_rejected_before_read_or_write(self):
        with patch(
            "aid.family_demo_intake._require_isolated_local_database",
            side_effect=CommandError("not isolated Heritage SQLite"),
        ):
            self.assertEqual(self.get_state().status_code, 404)
            self.assertEqual(self.submit().status_code, 404)
        self.assertFalse(AidApplication.objects.exists())
        self.assertFalse(AidFinancialProfile.objects.exists())

    @override_settings(CROWN_ENV="dev")
    def test_disabled_outside_local_is_fail_closed(self):
        self.assertEqual(self.get_state().status_code, 404)
        self.assertEqual(self.submit().status_code, 404)
        self.assertEqual(AidApplication.objects.count(), 0)

    @override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=False)
    def test_disabled_when_sandbox_session_off(self):
        self.assertEqual(self.get_state().status_code, 404)
        self.assertEqual(self.submit().status_code, 404)

    def test_admin_review_and_existing_offered_award_use_same_application(self):
        submitted = self.submit()
        self.assertEqual(submitted.status_code, 201)
        app = AidApplication.objects.get(pk=submitted.json()["application"]["id"])
        officer = UserAccount.objects.create_user(
            username="fictional-aid-officer", email="fictional-aid-officer@example.invalid", password="test-only", school=self.schools[0]
        )
        UserRole.objects.create(user=officer, school=self.schools[0], role_code="AID_DIRECTOR")
        grant, _ = CrownPermission.objects.get_or_create(code="financial_aid.view")
        RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=grant)
        client, headers = self.client_for(officer)
        review = client.get(
            "/api/v1/aid/admin/overview/",
            {"academic_year_id": str(self.years[0].pk)},
            **headers
        )
        self.assertEqual(review.status_code, 200, review.content)
        self.assertIn(app.pk, [row["id"] for row in review.json()["applications"]])
        award = AidAward.objects.create(
            school=self.schools[0], academic_year=self.years[0], student=self.students[0],
            aid_application=app, awarded_cents=25000, recommended_award_cents=25000,
            decision_status=AidAward.DECISION_OFFERED,
        )
        family_state = self.get_state().json()
        self.assertEqual(len(family_state["applications"][0]["awards"]), 1)
        exposed = family_state["applications"][0]["awards"][0]
        self.assertEqual(str(exposed["id"]), str(award.id))
        self.assertEqual(exposed["decision_status"], AidAward.DECISION_OFFERED)
        self.assertNotIn("ledger_entry_id", exposed)
        self.assertNotIn("explanation_json", exposed)
        self.assertEqual(AidAward.objects.count(), 1)

    def test_administrative_wizard_commits_fictional_offered_award_for_parent_application(self):
        submitted = self.submit()
        self.assertEqual(submitted.status_code, 201, submitted.content)
        app = AidApplication.objects.get(pk=submitted.json()["application"]["id"])
        officer = UserAccount.objects.create_user(
            username="fictional-wizard-officer",
            password="test-only",
            school=self.schools[0],
            email="fictional-wizard-officer@example.invalid",
        )
        UserRole.objects.create(user=officer, school=self.schools[0], role_code="AID_DIRECTOR")
        for code in ("financial_aid.view", "financial_aid.edit"):
            grant, _ = CrownPermission.objects.get_or_create(code=code)
            RolePermission.objects.get_or_create(role_code="AID_DIRECTOR", permission=grant)
        client, headers = self.client_for(officer)
        base = "/api/v1/aid-wizard/sessions/"
        created = client.post(base, {}, format="json", **headers)
        self.assertEqual(created.status_code, 201, created.content)
        session_url = base + str(created.json()["session_id"]) + "/"

        configured = client.post(
            session_url + "configure/",
            {"aid_year": self.years[0].name},
            format="json", **headers
        )
        self.assertEqual(configured.status_code, 200, configured.content)
        buckets = client.post(
            session_url + "buckets/", {"buckets": ["need"]},
            format="json", **headers
        )
        self.assertEqual(buckets.status_code, 200, buckets.content)
        awards = client.post(
            session_url + "awards/",
            {"awards": [{
                "application_id": app.id,
                "student_id": str(self.students[0].id),
                "bucket": "need",
                "amount": "250.00",
                "rationale": "Fictional case only",
            }]},
            format="json", **headers
        )
        self.assertEqual(awards.status_code, 200, awards.content)
        committed = client.post(
            session_url + "commit/", {"confirm": True},
            format="json", **headers
        )
        self.assertEqual(committed.status_code, 200, committed.content)
        self.assertEqual(committed.json()["awards_created"], 1)
        award = AidAward.objects.get(aid_application=app, student=self.students[0])
        self.assertEqual(award.decision_status, AidAward.DECISION_OFFERED)
        self.assertIsNone(award.ledger_entry_id)
        family_readback = self.get_state()
        self.assertEqual(family_readback.status_code, 200, family_readback.content)
        family_awards = family_readback.json()["applications"][0]["awards"]
        self.assertEqual(len(family_awards), 1)
        self.assertEqual(str(family_awards[0]["id"]), str(award.id))
        self.assertEqual(family_awards[0]["decision_status"], AidAward.DECISION_OFFERED)
        self.assertNotIn("explanation_json", family_awards[0])
        self.assertNotIn("ledger_entry_id", family_awards[0])
        self.assertEqual(AidAward.objects.count(), 1)
