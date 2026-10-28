"""Financial posting contracts, including actual PostgreSQL lock contention."""
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from threading import Event
from time import monotonic
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import close_old_connections, connection
from rest_framework.test import APIClient

from aid.models import AidAuditEvent, AidAward
from aid.services.ledger_bridge import ensure_accepted_award_credit
from core.models import AcademicYear, Family, HouseholdFamilyLink, LedgerEntry, School, Student, UserRole
from finance.models import ChartAccount
from households.models import Household
from ledger.models import Credit, LedgerAccount, Payment

pytestmark = pytest.mark.django_db


@pytest.fixture
def posting():
    school = School.objects.create(name="Posting integrity")
    year = AcademicYear.objects.create(school=school, name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
    family = Family.objects.create(school=school, family_name="Synthetic")
    student = Student.objects.create(school=school, family=family, student_number="P1", first_name="Test", last_name="Student", dob=date(2012, 1, 1))
    ChartAccount.objects.create(school=school, code="AID", name="Aid", account_type="INCOME")
    award = AidAward.objects.create(school=school, academic_year=year, student=student, awarded_cents=25000, decision_status=AidAward.DECISION_ACCEPTED)
    actor = get_user_model().objects.create_user(username="posting_director", school=school, is_staff=True)
    UserRole.objects.create(user=actor, school=school, role_code="AID_DIRECTOR")
    return school, award, actor


def link_household(school, award):
    household = Household.objects.create(school_id=school.pk, name="Synthetic household")
    HouseholdFamilyLink.objects.create(school=school, family=award.student.family, household_id=household.pk, source=HouseholdFamilyLink.SOURCE_MANUAL)
    return household


def post(posting, ids=None):
    school, award, actor = posting
    client = APIClient()
    client.force_login(actor)
    response = client.post("/api/director/actions/", {
        "action": "POST_ACCEPTED_AWARDS", "school_id": str(school.pk),
        "ids": ids if ids is not None else [str(award.pk)],
    }, format="json", HTTP_X_SCHOOL_ID=str(school.pk))
    assert response.status_code == 200
    return response.json()


@pytest.mark.parametrize("ambiguous", [False, True])
def test_deferred_retries_audit_once_then_reconcile_without_reposting(posting, ambiguous):
    school, award, _ = posting
    if ambiguous:
        link_household(school, award)
        link_household(school, award)
    assert post(posting)["posted_count"] == 1
    retry = post(posting)
    assert retry["posted_count"] == 0 and retry["errors"] is None
    event = AidAuditEvent.objects.get(school=school, entity_id=str(award.pk), action="STUDENT_ACCOUNT_CREDIT_DEFERRED")
    assert event.details_json["reason"] == ("household_family_link_ambiguous" if ambiguous else "household_family_link_missing")
    assert not LedgerAccount.objects.exists()
    assert not Credit.objects.exists()
    assert not Payment.objects.exists()
    award.refresh_from_db()
    original_entry = award.ledger_entry_id
    HouseholdFamilyLink.objects.filter(school=school).delete()
    household = link_household(school, award)
    for _ in range(2):
        result = post(posting)
        assert result["posted_count"] == 0 and result["errors"] is None
    award.refresh_from_db()
    assert award.ledger_entry_id == original_entry
    assert LedgerEntry.objects.count() == 1
    credit = Credit.objects.get()
    assert credit.amount == Decimal("250.00")
    assert credit.account.household_id == household.pk
    assert credit.source == Credit.SOURCE_FINANCIAL_AID
    assert not Payment.objects.exists()
    assert AidAuditEvent.objects.filter(action="STUDENT_ACCOUNT_CREDIT_DEFERRED").count() == 1
    assert AidAuditEvent.objects.filter(action="STUDENT_ACCOUNT_CREDIT_POSTED").count() == 1


def test_failure_after_credit_write_rolls_back_all_award_effects_and_continues(posting):
    school, award, _ = posting
    link_household(school, award)
    good = AidAward.objects.create(school=school, academic_year=award.academic_year, student=award.student, awarded_cents=12000, decision_status=AidAward.DECISION_ACCEPTED)
    def fail_after_write(**kwargs):
        result = ensure_accepted_award_credit(**kwargs)
        if kwargs["award"].pk == award.pk:
            assert result is not None
            raise RuntimeError("synthetic failure after credit and audit writes")
        return result
    with patch("crown_api.director_views.ensure_accepted_award_credit", side_effect=fail_after_write):
        result = post(posting, [str(award.pk), str(good.pk)])
    assert result["posted_count"] == 1
    assert result["errors"] == [{"award_id": str(award.pk), "error": "Internal processing error"}]
    award.refresh_from_db()
    good.refresh_from_db()
    assert award.ledger_entry_id is None and good.ledger_entry_id is not None
    assert LedgerEntry.objects.count() == Credit.objects.count() == 1
    assert Credit.objects.get().reference == f"aid_award:{good.pk}"
    assert not AidAuditEvent.objects.filter(entity_id=str(award.pk)).exists()
    assert not Payment.objects.exists()
    retried = post(posting)
    assert retried["posted_count"] == 1 and retried["errors"] is None
    assert LedgerEntry.objects.count() == Credit.objects.count() == 2
    assert not Payment.objects.exists()


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(connection.vendor != "postgresql", reason="Real row locks required; enforced by finance-postgresql CI")
def test_concurrent_director_retry_waits_and_posts_exactly_once(posting):
    school, award, _ = posting
    link_household(school, award)
    first_entered, release_first, second_started = Event(), Event(), Event()
    second_pid = []
    def paused_projection(**kwargs):
        if not first_entered.is_set():
            first_entered.set()
            assert release_first.wait(15), "First transaction was not released"
        return ensure_accepted_award_credit(**kwargs)
    def worker(second=False):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET statement_timeout = '20s'")
                cursor.execute("SET lock_timeout = '15s'")
                if second:
                    cursor.execute("SELECT pg_backend_pid()")
                    second_pid.append(cursor.fetchone()[0])
            if second:
                second_started.set()
            return post(posting)
        finally:
            connection.close()
    with patch("crown_api.director_views.ensure_accepted_award_credit", side_effect=paused_projection):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(worker)
            try:
                assert first_entered.wait(10)
                second = pool.submit(worker, True)
                assert second_started.wait(10)
                deadline = monotonic() + 5
                while monotonic() < deadline:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", second_pid)
                        waiting = cursor.fetchone()
                    if waiting == ("Lock",):
                        break
                    Event().wait(0.02)
                else:
                    pytest.fail("Competing API request did not wait on the PostgreSQL award lock")
            finally:
                release_first.set()
            results = [first.result(timeout=25), second.result(timeout=25)]
    assert [result["posted_count"] for result in results] == [1, 0]
    assert all(result["errors"] is None for result in results)
    assert LedgerEntry.objects.count() == Credit.objects.count() == 1
    assert Credit.objects.get().amount == Decimal("250.00")
    assert not Payment.objects.exists()
    assert AidAuditEvent.objects.filter(action="LEDGER_POSTED").count() == 1
    assert AidAuditEvent.objects.filter(action="STUDENT_ACCOUNT_CREDIT_POSTED").count() == 1
