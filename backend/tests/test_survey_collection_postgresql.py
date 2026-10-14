"""Real PostgreSQL lock ordering and concurrent respondent acceptance."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, Event
from time import monotonic
from unittest.mock import patch

import pytest
from django.db import close_old_connections, connection, transaction
from django.utils import timezone

from backend.tests.test_survey_intelligence_collection import collection, send
from survey_sentiment import collection as service
from survey_sentiment.models import SurveyCollectionReceipt, SurveyDefinition, SurveyRespondentGrant, SurveyResponse

pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(connection.vendor != "postgresql", reason="PostgreSQL row-lock integration; required in survey-postgresql CI"),
]


def worker(operation):
    close_old_connections()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET statement_timeout = '20s'")
            cursor.execute("SET lock_timeout = '10s'")
        return operation()
    finally:
        connection.close()


def parallel(*operations):
    start = Barrier(len(operations))
    def run(operation):
        start.wait(timeout=10)
        return operation()
    with ThreadPoolExecutor(max_workers=len(operations)) as executor:
        futures = [executor.submit(worker, lambda op=op: run(op)) for op in operations]
        return [future.result(timeout=25) for future in futures]


def rejection_or_receipt(c, payload=None):
    try:
        return send(c, payload)
    except service.CollectionRejected as exc:
        return exc


def wait_for_lock(pid):
    deadline = monotonic() + 5
    while monotonic() < deadline:
        with connection.cursor() as cursor:
            cursor.execute("SELECT wait_event_type FROM pg_stat_activity WHERE pid = %s", [pid])
            row = cursor.fetchone()
        if row == ("Lock",):
            return
        Event().wait(0.02)
    pytest.fail("Competing transaction did not wait on the expected PostgreSQL lock")


def assert_one_response():
    assert SurveyResponse.objects.count() == SurveyCollectionReceipt.objects.count() == 1
    assert SurveyResponse.objects.get().metadata_json == {}


def test_identical_concurrent_retries_both_return_same_receipt(collection):
    results = parallel(lambda: send(collection), lambda: send(collection))
    assert results[0] == results[1] == send(collection)
    assert_one_response()


def test_conflicting_concurrent_payloads_accept_exactly_one(collection):
    other = dict(collection[5], answers={"satisfaction": 5})
    results = parallel(lambda: rejection_or_receipt(collection), lambda: rejection_or_receipt(collection, other))
    assert len([result for result in results if isinstance(result, str)]) == 1
    errors = [result for result in results if isinstance(result, service.CollectionRejected)]
    assert len(errors) == 1 and "conflicts" in str(errors[0])
    assert_one_response()


def test_simultaneous_last_budget_attempt_has_one_winner(collection):
    SurveyRespondentGrant.objects.update(attempts=service.MAX_ATTEMPTS - 1)
    results = parallel(lambda: rejection_or_receipt(collection), lambda: rejection_or_receipt(collection))
    assert len([result for result in results if isinstance(result, str)]) == 1
    assert len([result for result in results if isinstance(result, service.CollectionRejected)]) == 1
    assert SurveyRespondentGrant.objects.get().attempts == service.MAX_ATTEMPTS
    assert_one_response()


@pytest.mark.parametrize("action", ["revoke", "close"])
def test_collection_commit_precedes_competing_revocation_or_closure(collection, action):
    entered = Event()
    release = Event()
    writer_started = Event()
    writer_pid = []
    persist = service.submit_anonymous_response
    def paused_persist(**kwargs):
        entered.set()
        assert release.wait(timeout=10)
        return persist(**kwargs)
    def writer():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            writer_pid.append(cursor.fetchone()[0])
        writer_started.set()
        if action == "revoke":
            service.revoke_respondent_grant(school_id=collection[0].pk, grant_id=SurveyRespondentGrant.objects.get().pk, issuer=collection[1])
        else:
            SurveyDefinition.objects.filter(pk=collection[2].pk).update(status="closed")
    with patch.object(service, "submit_anonymous_response", side_effect=paused_persist):
        with ThreadPoolExecutor(max_workers=2) as executor:
            collector = executor.submit(worker, lambda: send(collection))
            try:
                assert entered.wait(timeout=10)
                control = executor.submit(worker, writer)
                assert writer_started.wait(timeout=10)
                wait_for_lock(writer_pid[0])
            finally:
                release.set()
            receipt = collector.result(timeout=25)
            control.result(timeout=25)
    assert receipt == str(SurveyCollectionReceipt.objects.get().pk)
    with pytest.raises(service.CollectionRejected):
        send(collection)
    assert_one_response()


@pytest.mark.parametrize("action", ["revoke", "close"])
def test_committed_revocation_or_closure_prevents_waiting_collector(collection, action):
    held = Event()
    release = Event()
    collector_started = Event()
    collector_pid = []
    def control():
        with transaction.atomic():
            if action == "revoke":
                SurveyRespondentGrant.objects.update(revoked_at=timezone.now())
            else:
                SurveyDefinition.objects.filter(pk=collection[2].pk).update(status="closed")
            held.set()
            assert release.wait(timeout=10)
    def collector():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_backend_pid()")
            collector_pid.append(cursor.fetchone()[0])
        collector_started.set()
        return rejection_or_receipt(collection)
    with ThreadPoolExecutor(max_workers=2) as executor:
        controller = executor.submit(worker, control)
        try:
            assert held.wait(timeout=10)
            response = executor.submit(worker, collector)
            assert collector_started.wait(timeout=10)
            wait_for_lock(collector_pid[0])
        finally:
            release.set()
        controller.result(timeout=25)
        result = response.result(timeout=25)
    assert isinstance(result, service.CollectionRejected)
    assert not SurveyResponse.objects.exists() and not SurveyCollectionReceipt.objects.exists()
