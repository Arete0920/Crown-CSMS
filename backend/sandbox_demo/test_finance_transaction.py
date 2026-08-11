import pytest

from core.models import UserAccount
from finance.models import FinanceAllocation, FinanceObligation, FinancePayment, PaymentStatus
from ledger.models import Allocation as LedgerAllocation
from ledger.models import Payment as LedgerPayment
from sandbox_demo.finance import (
    SandboxFinanceError,
    apply_demo_payment,
    seed_heritage_finance_context,
    serialize_finance_state,
)
from sandbox_demo.services import create_sandbox_session, seed_heritage_flagship

pytestmark = pytest.mark.django_db(transaction=True)


def _user(email):
    return UserAccount.objects.get(username=email)


def _prepare(settings):
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    seed_heritage_flagship(reset=True)
    create_sandbox_session(persona_key="finance_director", school_key_or_id="heritage-core", guidance="guided")
    seed_heritage_finance_context()
    return _user("finance@heritage.example.org")


def test_finance_director_settles_reconciles_and_blocks_over_refund(settings):
    director = _prepare(settings)
    before = serialize_finance_state(director)
    assert before.family_account == "Reed Family"
    assert before.reconciliation_status == "open"
    assert before.remaining_cents == before.obligation_amount_cents
    assert before.voided_obligation_count >= 1
    assert before.voided_amount_excluded_cents == 12500

    balance_before = before.authoritative_balance_cents
    result = apply_demo_payment(director)
    assert result["reconciliation_status"] == "reconciled"
    assert result["exception_control_status"] == "verified"
    assert result["remaining_cents"] == 0
    assert result["authoritative_balance_cents"] == balance_before - before.obligation_amount_cents
    assert result["payment_history_count"] >= 1
    assert result["allocation_history_count"] >= 1
    assert result["voided_obligation_count"] >= 1
    assert result["voided_amount_excluded_cents"] == 12500
    assert result["voided_charges_excluded_from_balance"] is True
    assert result["over_refund_blocked"] is True
    assert result["external_payment_processed"] is False

    payment = FinancePayment.objects.get(id=result["payment_id"])
    assert payment.status == PaymentStatus.SETTLED
    assert FinanceAllocation.objects.filter(payment=payment).count() == 1
    assert LedgerPayment.objects.filter(reference=f"finance_payment:{payment.id}").exists()
    assert LedgerAllocation.objects.filter(payment__reference=f"finance_payment:{payment.id}").exists()

    replay = apply_demo_payment(director)
    assert replay["payment_id"] == result["payment_id"]
    assert replay["authoritative_balance_cents"] == result["authoritative_balance_cents"]
    assert FinanceAllocation.objects.filter(payment=payment).count() == 1


def test_finance_state_read_is_side_effect_free(settings):
    director = _prepare(settings)
    before_obligations = FinanceObligation.objects.count()
    before_payments = FinancePayment.objects.count()
    before_allocations = FinanceAllocation.objects.count()
    first = serialize_finance_state(director)
    second = serialize_finance_state(director)
    assert first == second
    assert FinanceObligation.objects.count() == before_obligations
    assert FinancePayment.objects.count() == before_payments
    assert FinanceAllocation.objects.count() == before_allocations


def test_non_finance_persona_cannot_use_finance_orchestration(settings):
    _prepare(settings)
    parent = _user("parent.reed@heritage.example.org")
    with pytest.raises(SandboxFinanceError, match="heritage_finance_director_required"):
        apply_demo_payment(parent)
