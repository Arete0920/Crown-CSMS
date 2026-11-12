"""Real database-concurrency proof for shared Jireh OFFERED award writers.

No hosted database, school, or account is used: all fixtures are synthetic.
"""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import connection, close_old_connections
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient

from aid.models import AidAward
from aid.tests.test_aid_api import _make_policy
from financial_aid_wizard.models import FinancialAidWizardSession
from financial_aid_wizard.tests.test_views import (
    BASE_URL, _headers, _make_application, _make_family,
    _make_school, _make_student, _make_user, _make_year,
)


@skipUnless(connection.vendor == "postgresql", "Requires PostgreSQL row locks")
class TestConcurrentWizardCommit(TransactionTestCase):
    """Both wizard and officer pathways must serialize by AidApplication."""

    def setUp(self):
        self.school = _make_school("Jireh Concurrent Wizard School")
        self.year = _make_year(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.application = _make_application(self.school, self.year, self.family)
        self.user = _make_user(self.school)
        self.award_data = {
            "application_id": self.application.pk,
            "student_id": str(self.student.pk),
            "bucket": "need", "amount": "200.00", "rationale": "Synthetic",
        }

    def new_session(self):
        return FinancialAidWizardSession.objects.create(
            school=self.school, created_by=self.user,
            aid_year=self.year.name, active_buckets=["need"],
            awards_config=[self.award_data],
            status=FinancialAidWizardSession.STATUS_AWARDS_STAGED,
        )

    def wizard(self, session_id, gate):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user=self.user)
            gate.wait(timeout=10)
            response = client.post(
                f"{BASE_URL}{session_id}/commit/", {"confirm": True},
                format="json", **_headers(self.school.pk),
            )
            return response.status_code, dict(response.data)
        finally:
            close_old_connections()

    def officer(self, gate):
        close_old_connections()
        try:
            client = APIClient()
            client.force_authenticate(user=self.user)
            gate.wait(timeout=10)
            response = client.post(
                "/api/aid/admin/recommend-award/", {
                    "application_id": self.application.pk,
                    "student_id": str(self.student.pk),
                    "bucket": AidAward.TYPE_NEED,
                    "gross_tuition_cents": 1_000_000,
                }, format="json", **_headers(self.school.pk),
            )
            return response.status_code
        finally:
            close_old_connections()

    def active_offer_count(self):
        return AidAward.objects.filter(
            school=self.school, academic_year=self.year,
            aid_application=self.application, student=self.student,
            award_type=AidAward.TYPE_NEED,
        ).exclude(decision_status=AidAward.DECISION_DECLINED).count()

    def test_two_wizard_sessions_same_application_only_one_offer(self):
        left, right = self.new_session(), self.new_session()
        gate = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(self.wizard, sid, gate) for sid in (left.pk, right.pk)]
            replies = [future.result(timeout=30) for future in futures]
        self.assertEqual(sorted(code for code, _ in replies), [200, 200])
        self.assertEqual(sorted(payload["awards_created"] for _, payload in replies), [0, 1])
        self.assertEqual(self.active_offer_count(), 1)

    def test_same_wizard_session_concurrent_commit_is_idempotent(self):
        session = self.new_session()
        gate = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as workers:
            futures = [workers.submit(self.wizard, session.pk, gate) for _ in range(2)]
            replies = [future.result(timeout=30) for future in futures]
        self.assertEqual([code for code, _ in replies], [200, 200])
        self.assertEqual([payload["awards_created"] for _, payload in replies], [1, 1])
        self.assertEqual(self.active_offer_count(), 1)

    def test_wizard_and_officer_concurrent_award_share_one_lock(self):
        _make_policy(self.school, self.year)
        session = self.new_session()
        gate = Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as workers:
            w = workers.submit(self.wizard, session.pk, gate)
            o = workers.submit(self.officer, gate)
            wizard_status, wizard_result = w.result(timeout=30)
            officer_status = o.result(timeout=30)
        self.assertEqual(wizard_status, 200)
        self.assertIn(officer_status, (201, 409))
        self.assertEqual(self.active_offer_count(), 1)
        self.assertEqual(
            (wizard_result["awards_created"], officer_status),
            (0, 201) if officer_status == 201 else (1, 409),
        )
\n\nclass TestWizardFinalizationAndReoffer(TestCase):
    """State immutability and decline semantics using only synthetic fixtures."""

    def setUp(self):
        self.school = _make_school("Jireh Finalization Guard School")
        self.year = _make_year(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.application = _make_application(self.school, self.year, self.family)
        self.user = _make_user(self.school)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.award_data = {
            "application_id": self.application.pk,
            "student_id": str(self.student.pk),
            "bucket": "need", "amount": "200.00", "rationale": "Synthetic",
        }

    def new_staged_session(self):
        return FinancialAidWizardSession.objects.create(
            school=self.school, created_by=self.user, aid_year=self.year.name,
            active_buckets=["need"], awards_config=[self.award_data],
            status=FinancialAidWizardSession.STATUS_AWARDS_STAGED,
        )

    def post(self, session, action, data):
        return self.client.post(
            f"{BASE_URL}{session.pk}/{action}/", data, format="json",
            **_headers(self.school.pk),
        )

    def test_committed_and_verified_sessions_cannot_be_reconfigured(self):
        session = self.new_staged_session()
        response = self.post(session, "commit", {"confirm": True})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["awards_created"], 1)
        for finalized in (FinancialAidWizardSession.STATUS_COMMITTED,
                          FinancialAidWizardSession.STATUS_VERIFIED):
            if finalized == FinancialAidWizardSession.STATUS_VERIFIED:
                self.assertEqual(self.post(session, "verify", {}).status_code, 200)
            for action, payload in (
                ("configure", {"aid_year": "2030-2031"}),
                ("buckets", {"buckets": ["mission"]}),
                ("awards", {"awards": []}),
            ):
                with self.subTest(status=finalized, action=action):
                    result = self.post(session, action, payload)
                    self.assertEqual(result.status_code, 409, result.data)
                    session.refresh_from_db()
                    self.assertEqual(session.status, finalized)
                    self.assertEqual(session.aid_year, self.year.name)
                    self.assertEqual(session.awards_config, [self.award_data])
        self.assertEqual(AidAward.objects.filter(aid_application=self.application).count(), 1)

    def test_precommit_reconfigure_invalidates_staged_awards(self):
        session = self.new_staged_session()
        response = self.post(session, "configure", {"aid_year": "2030-2031"})
        self.assertEqual(response.status_code, 200, response.data)
        session.refresh_from_db()
        self.assertEqual(session.status, FinancialAidWizardSession.STATUS_CONFIGURED)
        self.assertEqual(session.active_buckets, [])
        self.assertEqual(session.awards_config, [])
        self.assertIsNone(session.commit_result)
        self.assertEqual(self.post(session, "commit", {"confirm": True}).status_code, 409)
        self.assertFalse(AidAward.objects.filter(aid_application=self.application).exists())

    def test_declined_offer_can_be_reoffered_only_in_new_session(self):
        first = self.new_staged_session()
        response = self.post(first, "commit", {"confirm": True})
        self.assertEqual(response.status_code, 200, response.data)
        award = AidAward.objects.get(aid_application=self.application)
        # Exercise the audited decline path rather than changing status by hand.
        award.mark_declined_and_reverse(actor_user=self.user)
        award.refresh_from_db()
        self.assertEqual(award.decision_status, AidAward.DECISION_DECLINED)
        second = self.new_staged_session()
        response = self.post(second, "commit", {"confirm": True})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["awards_created"], 1)
        self.assertEqual(AidAward.objects.filter(aid_application=self.application).count(), 2)
        self.assertEqual(AidAward.objects.filter(
            aid_application=self.application,
        ).exclude(decision_status=AidAward.DECISION_DECLINED).count(), 1)
