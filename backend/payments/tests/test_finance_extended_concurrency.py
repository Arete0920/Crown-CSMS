from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from threading import Barrier

import pytest
from django.db import close_old_connections, connection

from aid.models import AidAward, AidBudgetTracker
from aid.services.ledger_bridge import approve_award
from core.models import AcademicYear, Family, HouseholdFamilyLink, School, Student, UserAccount
from finance.models import (
    ChartAccount,
    FinanceObligation,
    FinancePayment,
    MoneyStatus,
    ObligationType,
    PaymentStatus as LegacyPaymentStatus,
    Processor,
)
from households.models import Guardian as HouseholdGuardian, Household
from ledger.models import Credit, LedgerAccount
from payments.authority_services import (
    InvalidPaymentState,
    create_payment,
    request_refund,
    settle_payment,
)
from payments.models import CanonicalPaymentStatus, CanonicalRefundStatus, Payment, Refund


pytestmark = [
    pytest.mark.django_db(transaction=True),
    pytest.mark.skipif(
        connection.vendor != "postgresql",
        reason="Finance concurrency guarantees require PostgreSQL row-lock semantics.",
    ),
]


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
            connection.close()

    with ThreadPoolExecutor(max_workers=len(callables)) as pool:
        futures = [pool.submit(wrapped, fn) for fn in callables]
        return [future.result(timeout=30) for future in futures]


def _payment_fixture(*, amount_cents=10_000):
    school = School.objects.create(name="Extended Finance Concurrency School")
    payer = UserAccount.objects.create_user(
        username="extended_finance_concurrency_payer",
        password="pass",
        email="extended-finance-concurrency@test.example.com",
    )
    household = Household.objects.create(school_id=school.id, name="Extended Concurrency Household")
    HouseholdGuardian.objects.create(
        school_id=school.id,
        household=household,
        first_name="Extended",
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
        idempotency_key="extended-concurrent-payment",
        created_by=payer,
    )
    return school, payer, obligation, payment


def test_concurrent_create_payment_same_idempotency_key_returns_one_canonical_fact():
    school = School.objects.create(name="Canonical Payment Create Race School")

    def create_same():
        return create_payment(
            school_id=school.id,
            amount_cents=12_345,
            currency="USD",
            idempotency_key="parallel-create-payment",
        ).id

    results = _run_parallel([create_same, create_same])
    assert [state for state, _ in results] == ["ok", "ok"]
    ids = [value for _, value in results]
    assert ids[0] == ids[1]
    assert Payment.objects.filter(
        school_id=school.id,
        idempotency_key="parallel-create-payment",
    ).count() == 1


def test_settlement_refund_request_race_never_reserves_refund_before_settlement():
    school, payer, obligation, payment = _payment_fixture()
    allocation = [{"obligation_id": obligation.id, "amount_cents": 10_000}]

    def settle():
        row = Payment.objects.get(pk=payment.pk)
        return settle_payment(payment=row, allocations_payload=allocation).status

    def request():
        row = Payment.objects.get(pk=payment.pk)
        return request_refund(
            payment=row,
            amount_cents=2_500,
            idempotency_key="settlement-refund-race",
            created_by=payer,
        ).status

    results = _run_parallel([settle, request])
    settle_state, settle_value = results[0]
    refund_state, refund_value = results[1]

    assert settle_state == "ok"
    assert settle_value == CanonicalPaymentStatus.SETTLED
    assert refund_state in {"ok", "error"}
    if refund_state == "ok":
        assert refund_value == CanonicalRefundStatus.REQUESTED
    else:
        assert isinstance(refund_value, InvalidPaymentState)

    payment.refresh_from_db()
    assert payment.status == CanonicalPaymentStatus.SETTLED
    refunds = Refund.objects.filter(payment_id=payment.id)
    assert refunds.count() in {0, 1}
    if refunds.exists():
        assert refunds.get().status == CanonicalRefundStatus.REQUESTED
        assert refunds.get().amount_cents == 2_500


def test_concurrent_aid_approval_consumes_budget_once_and_posts_one_credit():
    school = School.objects.create(name="Aid Concurrency School")
    year = AcademicYear.objects.create(
        school=school,
        name="2026-27",
        start_date=date(2026, 8, 1),
        end_date=date(2027, 5, 31),
    )
    family = Family.objects.create(school=school, family_name="Concurrent Aid Family")
    student = Student.objects.create(
        school=school,
        family=family,
        student_number="AID-CONCURRENT-001",
        first_name="Avery",
        last_name="Concurrent",
        dob=date(2012, 3, 15),
    )
    household = Household.objects.create(school_id=school.id, name="Concurrent Aid Household")
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=household.id,
        family=family,
        source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    ChartAccount.objects.create(
        school=school,
        code="AID",
        name="Financial Aid",
        account_type="INCOME",
    )
    AidBudgetTracker.objects.create(
        school=school,
        academic_year=year,
        bucket=AidAward.TYPE_NEED,
        allocated_cents=1_000_000,
        awarded_cents=0,
    )
    award = AidAward.objects.create(
        school=school,
        academic_year=year,
        student=student,
        award_type=AidAward.TYPE_NEED,
        awarded_cents=25_000,
    )

    def approve():
        row = AidAward.objects.get(pk=award.pk)
        return approve_award(
            award=row,
            actor_user=None,
            reason="parallel approval proof",
        ).id

    results = _run_parallel([approve, approve])
    assert [state for state, _ in results] == ["ok", "ok"]
    assert [value for _, value in results] == [award.id, award.id]

    budget = AidBudgetTracker.objects.get(
        school=school,
        academic_year=year,
        bucket=AidAward.TYPE_NEED,
    )
    assert budget.awarded_cents == 25_000
    assert Credit.objects.filter(
        school_id=school.id,
        source=Credit.SOURCE_FINANCIAL_AID,
        reference=f"aid_award:{award.id}",
    ).count() == 1
