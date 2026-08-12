from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal
from threading import Barrier

import pytest
from django.db import IntegrityError, close_old_connections
from django.utils import timezone

from core.models import School, UserAccount
from finance.models import (
    FinanceAllocation,
    FinanceObligation,
    FinancePayment,
    MoneyStatus,
    ObligationType,
    PaymentStatus as LegacyPaymentStatus,
    Processor,
)
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import LedgerAccount
from payments.authority_services import (
    CanonicalOverRefundError,
    create_payment,
    request_refund,
    settle_payment,
)
from payments.models import (
    BankStatementEntry,
    BankStatementImport,
    CanonicalPaymentStatus,
    CanonicalRefundStatus,
    GatewayEvent,
    GatewayProvider,
    Payment,
    PayoutBankMatch,
    ProviderPayoutBatch,
    Refund,
)
from payments.reconciliation_ops import create_manual_payout_match


pytestmark = pytest.mark.django_db(transaction=True)


def _build_payment(*, amount_cents=10_000):
    school = School.objects.create(name="Finance Concurrency School")
    payer = UserAccount.objects.create_user(
        username="finance_concurrency_payer",
        password="pass",
        email="finance-concurrency@test.example.com",
    )
    household = Household.objects.create(school_id=school.id, name="Concurrency Household")
    HouseholdGuardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Concurrency",
        last_name="Guardian",
        email=payer.email,
        is_primary=True,
    )
    LedgerAccount.objects.create(school_id=school.id, household=household)
    obligation = FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.TUITION,
        status=MoneyStatus.OPEN,
        description="Concurrent tuition",
        due_date=date.today() + timedelta(days=30),
        amount_cents=amount_cents,
        currency="USD",
    )
    legacy = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=amount_cents,
        currency="USD",
        status=LegacyPaymentStatus.PENDING,
        processor=Processor.MANUAL,
        created_by=payer,
    )
    payment = create_payment(
        school_id=school.id,
        household_id=household.id,
        finance_payment_id=legacy.id,
        amount_cents=amount_cents,
        currency="USD",
        idempotency_key="concurrent-payment",
        created_by=payer,
    )
    return school, payer, obligation, legacy, payment


def _run_parallel(callables):
    barrier = Barrier(len(callables))

    def wrapped(fn):
        close_old_connections()
        barrier.wait(timeout=10)
        try:
            return ("ok", fn())
        except Exception as exc:
            return ("error", exc)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=len(callables)) as pool:
        return [future.result(timeout=30) for future in [pool.submit(wrapped, fn) for fn in callables]]


def test_simultaneous_settlement_is_single_posting_and_replay_safe():
    _school, _payer, obligation, legacy, payment = _build_payment()
    allocation = [{"obligation_id": obligation.id, "amount_cents": 10_000}]

    def settle():
        row = Payment.objects.get(pk=payment.pk)
        return settle_payment(payment=row, allocations_payload=allocation).status

    results = _run_parallel([settle, settle])
    assert [state for state, _ in results] == ["ok", "ok"]
    assert [value for _, value in results] == [CanonicalPaymentStatus.SETTLED] * 2

    payment.refresh_from_db()
    legacy.refresh_from_db()
    assert payment.status == CanonicalPaymentStatus.SETTLED
    assert legacy.status == LegacyPaymentStatus.SETTLED
    assert FinanceAllocation.objects.filter(
        payment=legacy,
        obligation=obligation,
        amount_cents=10_000,
    ).count() == 1


def test_simultaneous_refund_requests_cannot_overreserve_payment():
    school, payer, obligation, _legacy, payment = _build_payment()
    payment = settle_payment(
        payment=payment,
        allocations_payload=[{"obligation_id": obligation.id, "amount_cents": 10_000}],
    )

    def request(key):
        row = Payment.objects.get(pk=payment.pk)
        return request_refund(
            payment=row,
            amount_cents=6_000,
            idempotency_key=key,
            created_by=payer,
        ).id

    results = _run_parallel([
        lambda: request("concurrent-refund-a"),
        lambda: request("concurrent-refund-b"),
    ])
    successes = [value for state, value in results if state == "ok"]
    failures = [value for state, value in results if state == "error"]

    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], CanonicalOverRefundError)
    assert Refund.objects.filter(
        school_id=school.id,
        payment_id=payment.id,
        status=CanonicalRefundStatus.REQUESTED,
    ).count() == 1
    assert sum(
        Refund.objects.filter(payment_id=payment.id).values_list("amount_cents", flat=True)
    ) == 6_000


def test_duplicate_refund_idempotency_key_is_single_record_under_parallel_load():
    school, payer, obligation, _legacy, payment = _build_payment()
    payment = settle_payment(
        payment=payment,
        allocations_payload=[{"obligation_id": obligation.id, "amount_cents": 10_000}],
    )

    def request_same():
        row = Payment.objects.get(pk=payment.pk)
        refund = request_refund(
            payment=row,
            amount_cents=2_500,
            idempotency_key="same-refund-key",
            created_by=payer,
        )
        return refund.id

    results = _run_parallel([request_same, request_same])
    assert [state for state, _ in results] == ["ok", "ok"]
    ids = [value for _, value in results]
    assert ids[0] == ids[1]
    assert Refund.objects.filter(
        school_id=school.id,
        idempotency_key="same-refund-key",
    ).count() == 1


def test_duplicate_gateway_delivery_cannot_create_duplicate_event_fact():
    school = School.objects.create(name="Gateway Deduplication School")

    def receive():
        return GatewayEvent.objects.create(
            school_id=school.id,
            provider=GatewayProvider.COMPUWERX,
            event_id="evt-concurrent-1",
            event_type="payment.settled",
            raw_body="{}",
            payload={},
        ).id

    results = _run_parallel([receive, receive])
    successes = [value for state, value in results if state == "ok"]
    failures = [value for state, value in results if state == "error"]
    assert len(successes) == 1
    assert len(failures) == 1
    assert isinstance(failures[0], IntegrityError)
    assert GatewayEvent.objects.filter(
        provider=GatewayProvider.COMPUWERX,
        event_id="evt-concurrent-1",
    ).count() == 1


def test_reconciliation_workers_resolve_to_one_payout_bank_match():
    school = School.objects.create(name="Reconciliation Concurrency School")
    user = UserAccount.objects.create_user(
        username="reconciliation_concurrency_user",
        password="pass",
        email="reconciliation-concurrency@test.example.com",
    )
    payout = ProviderPayoutBatch.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        payout_id="payout-concurrent-1",
        status="settled",
        gross_amount=Decimal("100.00"),
        fee_amount=Decimal("2.00"),
        net_amount=Decimal("98.00"),
        currency="USD",
        settled_at=timezone.now(),
    )
    statement_import = BankStatementImport.objects.create(
        school_id=school.id,
        source_name="concurrent.csv",
        source_sha256="a" * 64,
        status="processed",
        row_count=1,
    )
    bank_entry = BankStatementEntry.objects.create(
        school_id=school.id,
        statement_import=statement_import,
        posted_date=date.today(),
        description="Provider payout",
        reference="payout-concurrent-1",
        amount=Decimal("98.00"),
        currency="USD",
    )

    def match():
        return create_manual_payout_match(
            school_id=school.id,
            payout_batch=ProviderPayoutBatch.objects.get(pk=payout.pk),
            bank_entry=BankStatementEntry.objects.get(pk=bank_entry.pk),
            user=user,
            note="parallel reconciliation proof",
        ).id

    results = _run_parallel([match, match])
    assert [state for state, _ in results] == ["ok", "ok"]
    ids = [value for _, value in results]
    assert ids[0] == ids[1]
    assert PayoutBankMatch.objects.filter(payout_batch=payout, bank_entry=bank_entry).count() == 1
    bank_entry.refresh_from_db()
    assert bank_entry.is_matched is True
