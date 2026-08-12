from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

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
from ledger.models import Allocation as LedgerAllocation
from ledger.models import LedgerAccount, Payment as LedgerPayment
from payments.authority_services import (
    CanonicalOverRefundError,
    create_payment,
    request_refund,
    settle_payment,
)
from payments.models import CanonicalPaymentStatus, Payment, Refund


pytestmark = pytest.mark.django_db(transaction=True)


def _require_postgresql():
    if connection.vendor != "postgresql":
        pytest.skip("row-lock concurrency proof requires PostgreSQL")


def _user(username):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
    )


def _payment_fixture(prefix="concurrency"):
    school = School.objects.create(name=f"{prefix} school")
    payer = _user(f"{prefix}_payer")
    household = Household.objects.create(school_id=school.id, name=f"{prefix} household")
    HouseholdGuardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Concurrent",
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
        description="Concurrency tuition",
        due_date=date.today() + timedelta(days=30),
        amount_cents=10_000,
        currency="USD",
    )
    legacy = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=10_000,
        currency="USD",
        status=LegacyPaymentStatus.PENDING,
        processor=Processor.MANUAL,
        created_by=payer,
    )
    payment = create_payment(
        school_id=school.id,
        household_id=household.id,
        finance_payment_id=legacy.id,
        amount_cents=10_000,
        idempotency_key=f"{prefix}-payment",
        created_by=payer,
    )
    return school, payer, household, obligation, legacy, payment


def test_concurrent_settlement_posts_money_once():
    _require_postgresql()
    school, _, _, obligation, legacy, payment = _payment_fixture("settle-race")
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            candidate = Payment.objects.get(pk=payment.pk)
            barrier.wait(timeout=10)
            settled = settle_payment(
                payment=candidate,
                allocations_payload=[
                    {"obligation_id": obligation.id, "amount_cents": 10_000}
                ],
            )
            return settled.status
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _: worker(), range(2)))

    assert results == [CanonicalPaymentStatus.SETTLED, CanonicalPaymentStatus.SETTLED]
    legacy.refresh_from_db()
    assert legacy.status == LegacyPaymentStatus.SETTLED
    assert FinanceAllocation.objects.filter(payment=legacy).count() == 1
    assert LedgerPayment.objects.filter(
        school_id=school.id,
        reference=f"finance_payment:{legacy.id}",
    ).count() == 1
    assert LedgerAllocation.objects.filter(
        payment__reference=f"finance_payment:{legacy.id}"
    ).count() == 1


def test_concurrent_refund_reservations_cannot_over_refund():
    _require_postgresql()
    _, _, _, obligation, _, payment = _payment_fixture("refund-race")
    payment = settle_payment(
        payment=payment,
        allocations_payload=[{"obligation_id": obligation.id, "amount_cents": 10_000}],
    )
    barrier = Barrier(2)

    def worker(key):
        close_old_connections()
        try:
            candidate = Payment.objects.get(pk=payment.pk)
            barrier.wait(timeout=10)
            try:
                refund = request_refund(
                    payment=candidate,
                    amount_cents=6_000,
                    idempotency_key=key,
                )
                return ("created", refund.pk)
            except CanonicalOverRefundError:
                return ("over_refund", None)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(worker, ["refund-race-a", "refund-race-b"]))

    assert sorted(result[0] for result in results) == ["created", "over_refund"]
    assert Refund.objects.filter(payment=payment).count() == 1
    assert Refund.objects.get(payment=payment).amount_cents == 6_000


def test_concurrent_payment_idempotency_returns_one_canonical_fact():
    _require_postgresql()
    school = School.objects.create(name="Create race school")
    payer = _user("create_race_payer")
    household = Household.objects.create(school_id=school.id, name="Create race household")
    legacy = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=5_000,
        currency="USD",
        status=LegacyPaymentStatus.PENDING,
        processor=Processor.MANUAL,
        created_by=payer,
    )
    barrier = Barrier(2)

    def worker():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            payment = create_payment(
                school_id=school.id,
                household_id=household.id,
                finance_payment_id=legacy.id,
                amount_cents=5_000,
                idempotency_key="create-race-key",
                created_by=payer,
            )
            return payment.pk
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as executor:
        ids = list(executor.map(lambda _: worker(), range(2)))

    assert ids[0] == ids[1]
    assert Payment.objects.filter(
        school_id=school.id,
        idempotency_key="create-race-key",
    ).count() == 1
