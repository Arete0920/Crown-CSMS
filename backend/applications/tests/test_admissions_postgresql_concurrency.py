"""Actual PostgreSQL two-worker admissions fee idempotency proof.

The SQLite backend does not implement select_for_update; this test must not
claim concurrency acceptance on SQLite. CI runs it against PostgreSQL 16.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase, override_settings
from rest_framework.test import APIClient

from applications.models import AdmissionsSubmissionReceipt, Application, Applicant
from core.models import AcademicYear, School
from fee_schedule_wizard.models import FeeLine, FeeSchedule
from finance.models import FinanceInvoice, FinanceObligation


def _admissions_payload():
    return {
        "inquiry": {
            "campus": "Admissions Concurrency School",
            "startTerm": "2026-2027",
            "heardAbout": "Church referral",
        },
        "family": {
            "guardians": [{
                "relationship": "Mother",
                "guardianName": "Concurrency Parent",
                "email": "concurrent.parent@example.com",
                "phone": "555-0101",
                "isPrimary": True,
            }],
            "churchAffiliation": "Attend regularly",
        },
        "students": [{
            "firstName": "Alex",
            "lastName": "Parent",
            "gradeApplyingFor": "5",
            "currentSchool": "Public school",
        }],
        "mission": {
            "covenantPartnership": True,
            "discipleshipCommitment": True,
            "serviceMindset": True,
        },
        "documents": {
            "transcriptReady": True,
            "recommendationsReady": True,
            "immunizationReady": True,
        },
        "attestations": {
            "informationAccurate": True,
            "missionPartnershipUnderstood": True,
            "communicationOptIn": True,
        },
        "applicationFee": {
            "policyAccepted": True,
            "waiverRequested": False,
        },
    }


class AdmissionsSubmissionPostgresConcurrencyTests(TransactionTestCase):
    """Two independent connections, one tenant + idempotency key."""

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Requires PostgreSQL row locking; SQLite is not equivalent")
        self.school = School.objects.create(name="Admissions Concurrency School")
        AcademicYear.objects.create(
            school=self.school, name="2026-2027",
            start_date="2026-08-01", end_date="2027-05-31", is_current=True,
        )
        schedule = FeeSchedule.objects.create(
            school=self.school, name="Admissions", term="2026-2027",
            effective_date="2026-08-01", is_active=True,
        )
        for code, cents in (
            ("admissions_first_child", 8500),
            ("admissions_additional_child", 5000),
        ):
            FeeLine.objects.create(
                fee_schedule=schedule,
                code=code,
                label=code,
                amount_cents=cents,
                kind=FeeLine.KIND_FEE,
                frequency=FeeLine.FREQ_ONE_TIME,
                is_required=True,
            )

    @override_settings(DEBUG=True)
    def test_two_workers_same_key_persist_only_one_household_invoice(self):
        barrier = Barrier(2)
        request_payload = _admissions_payload()
        key = "admissions-postgres-concurrent-replay"

        def post_from_separate_connection():
            close_old_connections()
            try:
                client = APIClient()
                barrier.wait(timeout=15)
                response = client.post(
                    "/api/v1/admissions/submit/",
                    deepcopy(request_payload),
                    format="json",
                    HTTP_IDEMPOTENCY_KEY=key,
                    HTTP_X_SCHOOL_ID=str(self.school.pk),
                )
                body = response.json()
                return response.status_code, body, response.get("X-Idempotent-Replay")
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(post_from_separate_connection)
            second = pool.submit(post_from_separate_connection)
            results = [first.result(timeout=90), second.result(timeout=90)]

        # Show the actual server responses if routing, auth or concurrency fails.
        self.assertEqual(sorted(result[0] for result in results), [200, 201], results)
        self.assertEqual(
            [result[2] for result in results].count("true"), 1, results,
        )
        self.assertEqual(results[0][1]["application_ids"], results[1][1]["application_ids"])
        self.assertEqual(
            AdmissionsSubmissionReceipt.objects.filter(school_id=self.school.id, idempotency_key=key).count(),
            1,
        )
        self.assertEqual(Application.objects.filter(school_id=self.school.id).count(), 1)
        self.assertEqual(Applicant.objects.filter(school_id=self.school.id).count(), 1)
        self.assertEqual(FinanceObligation.objects.filter(school=self.school).count(), 1)
        invoices = FinanceInvoice.objects.filter(school=self.school)
        self.assertEqual(invoices.count(), 1)
        self.assertEqual(invoices.get().total_cents, 8500)
        self.assertEqual(invoices.get().lines.count(), 1)



class SandboxParentEnrollmentPostgresConcurrencyTests(TransactionTestCase):
    """Real PostgreSQL two-connection replay of the same fictional parent POST."""

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Requires real PostgreSQL locking, not SQLite")
        from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
        from sandbox_demo.parent_enrollment import seed_parent_enrollment_scenario
        from sandbox_demo.services import ensure_demo_school, ensure_persona_user

        self.school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
        self.parent = ensure_persona_user(self.school, SANDBOX_PERSONAS["parent"])
        ensure_persona_user(self.school, SANDBOX_PERSONAS["school_admin"])
        self.application_id = seed_parent_enrollment_scenario()[
            "parent_enrollment_application_id"
        ]

    @override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
    def test_two_parent_posts_commit_exactly_one_student_and_completion(self):
        from admissions.models import AdmissionsApplication
        from applications.models import ApplicationEvent, EnrollmentContract
        from core.models import Enrollment, HouseholdFamilyLink, StudentIdentityLink
        from enrollment_conversion_wizard.models import EnrollmentConversionWizardSession

        barrier = Barrier(2)

        def post_from_separate_connection():
            close_old_connections()
            try:
                client = APIClient()
                client.force_authenticate(user=self.parent)
                client.credentials(HTTP_X_SCHOOL_ID=str(self.school.id))
                barrier.wait(timeout=15)
                response = client.post(
                    "/api/v1/sandbox/parent/enrollment/",
                    {
                        "application_id": self.application_id,
                        "accepted_terms": True,
                    },
                    format="json",
                )
                return response.status_code, dict(response.data)
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(post_from_separate_connection)
            second = pool.submit(post_from_separate_connection)
            results = [first.result(timeout=90), second.result(timeout=90)]

        self.assertEqual([status for status, _ in results], [200, 200], results)
        self.assertEqual(
            {body["child_id"] for _, body in results},
            {results[0][1]["child_id"]},
        )
        for _, body in results:
            self.assertEqual(body["applicant_to_student_status"], "completed")
            self.assertEqual(body["classroom_readiness_status"], "completed")
            self.assertEqual(body["parent_portal_activation_status"], "completed")
            self.assertIs(body["demo_payment_processed"], False)

        app = Application.objects.get(pk=self.application_id)
        applicant = Applicant.objects.get(application=app)
        link = StudentIdentityLink.objects.get(
            school_id=self.school.id, compatibility_student_id=applicant.student_id,
        )
        self.assertEqual(
            link.evidence_reference,
            f"application:{app.id}:applicant:{applicant.id}",
        )
        self.assertEqual(
            HouseholdFamilyLink.objects.filter(
                school_id=self.school.id, household_id=app.household_id
            ).count(),
            1,
        )
        self.assertEqual(
            StudentIdentityLink.objects.filter(
                school_id=self.school.id,
                compatibility_student_id=applicant.student_id,
            ).count(),
            1,
        )
        self.assertEqual(
            Enrollment.objects.filter(
                school_id=self.school.id, student=link.core_student
            ).count(),
            1,
        )
        self.assertEqual(
            AdmissionsApplication.objects.filter(
                school=self.school,
                student=link.core_student,
                notes_internal__contains=f"canonical_application_id={app.id}",
            ).count(),
            1,
        )
        self.assertEqual(
            EnrollmentContract.objects.filter(application=app).count(), 1
        )
        self.assertEqual(
            EnrollmentConversionWizardSession.objects.filter(school=self.school).count(),
            1,
        )
        for event_type in (
            "parent_enrollment_agreement_signed",
            "sandbox_demo_deposit_simulated",
            "enrollment_confirmed",
            "classroom_readiness_completed",
            "parent_portal_activated",
        ):
            self.assertEqual(
                ApplicationEvent.objects.filter(
                    application=app, event_type=event_type,
                ).count(),
                1,
                event_type,
            )



class CanonicalDecisionPostgresConcurrencyTests(TransactionTestCase):
    """Lock the canonical application before creating student and fee evidence."""

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("Requires PostgreSQL row-lock semantics")
        from datetime import date
        from django.contrib.auth import get_user_model
        from core.models import Family, HouseholdFamilyLink
        from households.models import Household
        from applications.models import ApplicationStatus

        self.school = School.objects.create(name="Concurrent Decision School")
        household = Household.objects.create(
            school_id=self.school.id, name="Concurrent Decision Household"
        )
        family = Family.objects.create(
            school=self.school, family_name="Concurrent Decision Family"
        )
        HouseholdFamilyLink.objects.create(
            school=self.school, household_id=household.id, family=family,
            source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
        )
        self.application = Application.objects.create(
            school_id=self.school.id,
            household=household,
            status=ApplicationStatus.SUBMITTED,
        )
        self.applicant = Applicant.objects.create(
            school_id=self.school.id,
            application=self.application,
            first_name="Row",
            last_name="Lock",
            grade_applying_for="4",
            dob=date(2016, 4, 10),
        )
        User = get_user_model()
        self.user = User.objects.create_user(
            username="concurrent-decision-test", password="TestOnlySecure!"
        )
        self.user.school = self.school
        self.user.save(update_fields=["school"])

    def test_two_acceptance_posts_create_exactly_one_student_and_fee(self):
        from django.test import Client
        from applications.models import ApplicationEvent, ApplicationStatus
        from core.models import Student as CanonicalStudent, StudentIdentityLink
        from ledger.models import Charge, LedgerAccount

        barrier = Barrier(2)
        request_payload = {
            "decision": "ACCEPT",
            "student_numbers": {str(self.applicant.id): "S-CONCURRENT-001"},
            "enrollment_fee": "25.00",
        }

        def post_in_own_connection():
            close_old_connections()
            try:
                client = Client()
                client.force_login(self.user)
                barrier.wait(timeout=15)
                response = client.post(
                    f"/api/v1/applications/{self.application.id}/decision/",
                    data=deepcopy(request_payload),
                    content_type="application/json",
                )
                return response.status_code
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(post_in_own_connection) for _ in range(2)]
            statuses = sorted(f.result(timeout=90) for f in futures)

        self.assertEqual(statuses, [200, 400])
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, ApplicationStatus.DECIDED)
        self.assertEqual(
            CanonicalStudent.objects.filter(school=self.school).count(), 1,
        )
        self.assertEqual(
            StudentIdentityLink.objects.filter(school=self.school).count(), 1,
        )
        self.assertEqual(
            ApplicationEvent.objects.filter(
                application=self.application, event_type="APPLICATION_ACCEPTED",
            ).count(), 1,
        )
        self.assertEqual(
            LedgerAccount.objects.filter(
                school_id=self.school.id, household_id=self.application.household_id,
            ).count(), 1,
        )
        self.assertEqual(
            Charge.objects.filter(
                school_id=self.school.id, account__household_id=self.application.household_id,
            ).count(), 1,
        )
