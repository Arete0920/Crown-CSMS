"""No duplicate Jireh offers after ambiguous POST outcome (synthetic school only)."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless

from django.db import connection, close_old_connections
from django.test import Client, TestCase, TransactionTestCase
from aid.models import AidAward, AidBudgetTracker, AidAuditEvent
from core.models import LedgerEntry
from aid.tests.test_aid_api import (
    _make_school, _make_ay, _make_family, _make_student, _make_staff_user,
    _make_application, _make_policy, _json_post,
)


class TestRecommendationRetryGuard(TestCase):
    def setUp(self):
        self.school = _make_school("Recommendation Retry School")
        self.year = _make_ay(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.application = _make_application(self.school, self.year, self.family)
        self.policy = _make_policy(self.school, self.year)
        self.user = _make_staff_user(self.school, "retry_guard")
        self.client.force_login(self.user)
        self.url = "/api/aid/admin/recommend-award/"

    def send(self, *, bucket=AidAward.TYPE_NEED):
        return _json_post(self.client, self.url, {
            "application_id": str(self.application.pk),
            "student_id": str(self.student.pk),
            "bucket": bucket,
            "gross_tuition_cents": 1_000_000,
        }, self.school)

    def test_first_offer_created_retry_conflicts_without_financial_mutation(self):
        initial = self.send()
        self.assertEqual(initial.status_code, 201, initial.content)
        baseline = {
            "awards": AidAward.objects.count(),
            "budgets": list(AidBudgetTracker.objects.values_list("pk", "allocated_cents", "awarded_cents")),
            "ledger": LedgerEntry.objects.count(),
            "audit": AidAuditEvent.objects.count(),
        }
        retry = self.send()
        self.assertEqual(retry.status_code, 409, retry.content)
        self.assertEqual(AidAward.objects.count(), baseline["awards"])
        self.assertEqual(list(AidBudgetTracker.objects.values_list("pk", "allocated_cents", "awarded_cents")), baseline["budgets"])
        self.assertEqual(LedgerEntry.objects.count(), baseline["ledger"])
        self.assertEqual(AidAuditEvent.objects.count(), baseline["audit"])

    def test_declined_offer_allows_new_decision(self):
        first = self.send()
        self.assertEqual(first.status_code, 201, first.content)
        Award = AidAward
        Award.objects.filter(pk=first.json()["award"]["id"]).update(decision_status=Award.DECISION_DECLINED)
        second = self.send()
        self.assertEqual(second.status_code, 201, second.content)
        self.assertEqual(Award.objects.filter(aid_application=self.application).count(), 2)

    def test_other_bucket_does_not_conflict(self):
        self.assertEqual(self.send().status_code, 201)
        self.assertEqual(self.send(bucket=AidAward.TYPE_MISSION).status_code, 201)
        self.assertEqual(AidAward.objects.filter(aid_application=self.application).count(), 2)

@skipUnless(connection.vendor == "postgresql", "Row-lock concurrency requires PostgreSQL")
class TestRecommendationConcurrentRetry(TransactionTestCase):
    """Two independent PostgreSQL transactions must serialize one application."""

    def setUp(self):
        self.school = _make_school("Concurrent Retry School")
        self.year = _make_ay(self.school)
        self.family = _make_family(self.school)
        self.student = _make_student(self.school, self.family)
        self.application = _make_application(self.school, self.year, self.family)
        _make_policy(self.school, self.year)
        self.user = _make_staff_user(self.school, "concurrent_retry")

    def test_two_post_requests_create_one_active_offer(self):
        gate = Barrier(2)

        def send():
            close_old_connections()
            try:
                client = Client()
                client.force_login(self.user)
                gate.wait(timeout=10)
                return _json_post(client, "/api/aid/admin/recommend-award/", {
                    "application_id": str(self.application.pk),
                    "student_id": str(self.student.pk),
                    "bucket": AidAward.TYPE_NEED,
                    "gross_tuition_cents": 1_000_000,
                }, self.school).status_code
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as workers:
            attempts = [workers.submit(send) for _ in range(2)]
            codes = [work.result(timeout=30) for work in attempts]

        self.assertEqual(sorted(codes), [201, 409])
        self.assertEqual(AidAward.objects.filter(
            aid_application=self.application, student=self.student,
            award_type=AidAward.TYPE_NEED,
        ).exclude(decision_status=AidAward.DECISION_DECLINED).count(), 1)

