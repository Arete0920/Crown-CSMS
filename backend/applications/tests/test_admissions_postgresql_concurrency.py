"""Actual PostgreSQL two-worker admissions fee idempotency proof.

The SQLite backend does not implement select_for_update; this test must not
claim concurrency acceptance on SQLite. CI runs it against PostgreSQL 16.
"""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier

from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase
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
