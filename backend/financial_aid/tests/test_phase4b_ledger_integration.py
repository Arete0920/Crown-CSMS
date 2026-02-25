# backend/financial_aid/tests/test_phase4b_ledger_integration.py
"""
Phase 4B: ledger-integrated financial aid acceptance tests.

Scenario under test
-------------------
Household receives a $10,000 tuition charge linked to a BillingRun Invoice.
A $3,000 AidAward is applied via apply_financial_aid_to_billing_run().
This should:
  1. Create a Payment(source='FINANCIAL_AID', amount=3000)
  2. Create an Allocation(payment→charge, amount=3000)
  3. Record an idempotency AidAuditEvent
  4. Leave account_balance == 7000
Then an external payment of $7,000 clears the balance to $0.

Also verifies billing_run_summary() and build_account_statement() reflect the aid.
"""
import uuid
from decimal import Decimal

import pytest

from core.models import School
from households.models import Household
from ledger.models import LedgerAccount, Charge, Payment, Allocation
from ledger.services import account_balance, build_account_statement
from billing.models import BillingRun, Invoice
from financial_aid.models import FinancialAidApplication, AidAward, AidAuditEvent
from financial_aid.services import apply_financial_aid_to_billing_run

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _sid():
    """Create a fresh School and return its UUID (required by Charge signal)."""
    sid = uuid.uuid4()
    School.objects.get_or_create(id=sid, defaults={"name": f"Phase4B-{sid}"})
    return sid


def _make_household(sid):
    return Household.objects.create(school_id=sid, name=f"HH-{uuid.uuid4()}")


def _make_ledger_account(sid, hh):
    return LedgerAccount.objects.create(school_id=sid, household=hh)


def _make_billing_run(sid, term="2025-26"):
    return BillingRun.objects.create(
        school_id=sid,
        term=term,
        description="Tuition billing",
        amount_per_student=Decimal("10000.00"),
    )


def _make_invoice_with_charge(sid, run, hh, acct, tuition_amount=Decimal("10000.00")):
    """Create an Invoice + the matching Charge, wire invoice.ledger_charge_id."""
    charge = Charge.objects.create(
        school_id=sid,
        account=acct,
        description="Tuition",
        amount=tuition_amount,
    )
    invoice = Invoice.objects.create(
        school_id=sid,
        billing_run=run,
        household=hh,
        total_amount=tuition_amount,
        ledger_charge_id=charge.id,
    )
    return invoice, charge


def _make_aid_award(sid, hh, amount=Decimal("3000.00")):
    """
    Create a decided FinancialAidApplication + an AidAward linked to it.
    AidAward presence implies approval (no status field on financial_aid.AidAward).
    """
    app = FinancialAidApplication.objects.create(
        school_id=sid,
        household_id=hh.id,
        academic_year="2025-26",
        status="decided",
        household_income=Decimal("50000.00"),
        household_size=4,
    )
    award = AidAward.objects.create(
        school_id=sid,
        application=app,
        bucket="need",
        amount=amount,
        rationale="Need-based award for Phase 4B test",
    )
    return app, award


# ---------------------------------------------------------------------------
# Test 1: Core happy path
# ---------------------------------------------------------------------------

def test_apply_aid_creates_payment_and_allocation():
    sid = _sid()
    hh = _make_household(sid)
    acct = _make_ledger_account(sid, hh)
    run = _make_billing_run(sid)
    invoice, charge = _make_invoice_with_charge(sid, run, hh, acct)
    _app, award = _make_aid_award(sid, hh, amount=Decimal("3000.00"))

    result = apply_financial_aid_to_billing_run(
        school_id=sid,
        billing_run_id=run.id,
    )

    assert result["payments_created"] == 1, result
    assert result["allocations_created"] == 1, result
    assert result["events_created"] == 1, result
    assert Decimal(result["disbursed_total"]) == Decimal("3000.00"), result

    # Verify ledger objects
    pay = Payment.objects.get(school_id=sid, account=acct, source="FINANCIAL_AID")
    assert pay.amount == Decimal("3000.00")
    assert str(award.id) in pay.reference

    alloc = Allocation.objects.get(school_id=sid, payment=pay, charge=charge)
    assert alloc.amount == Decimal("3000.00")

    # Verify idempotency event
    evt = AidAuditEvent.objects.get(
        school_id=sid,
        event_type="DISBURSED_TO_BILLING_RUN",
        entity_id=award.id,
    )
    assert evt.message == str(run.id)


# ---------------------------------------------------------------------------
# Test 2: Idempotency — calling twice must not double-post
# ---------------------------------------------------------------------------

def test_apply_aid_is_idempotent():
    sid = _sid()
    hh = _make_household(sid)
    acct = _make_ledger_account(sid, hh)
    run = _make_billing_run(sid)
    _make_invoice_with_charge(sid, run, hh, acct)
    _app, _award = _make_aid_award(sid, hh, amount=Decimal("2000.00"))

    result1 = apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
    result2 = apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)

    # Second call should create nothing new
    assert result1["payments_created"] == 1
    assert result2["payments_created"] == 0, "Second call must skip already-disbursed awards"
    assert result2["disbursed_total"] == "0.00", result2

    # Total payments in DB still 1
    assert Payment.objects.filter(school_id=sid, source="FINANCIAL_AID").count() == 1


# ---------------------------------------------------------------------------
# Test 3: account_balance reflects aid reduction
# ---------------------------------------------------------------------------

def test_account_balance_reflects_aid():
    sid = _sid()
    hh = _make_household(sid)
    acct = _make_ledger_account(sid, hh)
    run = _make_billing_run(sid)
    _make_invoice_with_charge(sid, run, hh, acct, tuition_amount=Decimal("10000.00"))
    _make_aid_award(sid, hh, amount=Decimal("3000.00"))

    apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)

    bal = account_balance(acct)
    assert bal == Decimal("7000.00"), f"Expected 7000.00, got {bal}"


# ---------------------------------------------------------------------------
# Test 4: billing_run_summary reports gross/aid/net correctly
# ---------------------------------------------------------------------------

def test_billing_run_summary_net_due_correct():
    from ledger.services import billing_run_summary

    sid = _sid()
    hh = _make_household(sid)
    acct = _make_ledger_account(sid, hh)
    run = _make_billing_run(sid)
    _make_invoice_with_charge(sid, run, hh, acct, tuition_amount=Decimal("10000.00"))
    _make_aid_award(sid, hh, amount=Decimal("3000.00"))

    apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)

    summary = billing_run_summary(school_id=sid, billing_run=run)
    assert Decimal(summary["gross_total"]) == Decimal("10000.00"), summary
    assert Decimal(summary["aid_applied_total"]) == Decimal("3000.00"), summary
    assert Decimal(summary["net_due_total"]) == Decimal("7000.00"), summary


# ---------------------------------------------------------------------------
# Test 5: build_account_statement contains FINANCIAL_AID entry
# ---------------------------------------------------------------------------

def test_account_statement_shows_financial_aid_entry():
    sid = _sid()
    hh = _make_household(sid)
    acct = _make_ledger_account(sid, hh)
    run = _make_billing_run(sid)
    _make_invoice_with_charge(sid, run, hh, acct)
    _make_aid_award(sid, hh, amount=Decimal("3000.00"))

    apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)

    stmt = build_account_statement(school_id=sid, account=acct)

    sources = [e.get("source") for e in stmt["entries"]]
    assert "FINANCIAL_AID" in sources, f"Expected FINANCIAL_AID in statement sources: {sources}"

    # Running balance at end of statement matches account_balance
    final_balance = Decimal(stmt["balance"])
    assert final_balance == account_balance(acct), (
        f"Statement balance {final_balance} != account_balance {account_balance(acct)}"
    )


# ---------------------------------------------------------------------------
# Test 6: Full scenario — charge → aid → external payment → zero balance
# ---------------------------------------------------------------------------

def test_full_scenario_charge_aid_payment_zero_balance():
    """
    The complete financial journey:
      $10,000 tuition charge
      $3,000 aid award applied
      $7,000 external payment
      Final balance: $0.00
    """
    sid = _sid()
    hh = _make_household(sid)
    acct = _make_ledger_account(sid, hh)
    run = _make_billing_run(sid)
    invoice, charge = _make_invoice_with_charge(
        sid, run, hh, acct, tuition_amount=Decimal("10000.00")
    )
    _make_aid_award(sid, hh, amount=Decimal("3000.00"))

    # Step 1: apply aid
    result = apply_financial_aid_to_billing_run(school_id=sid, billing_run_id=run.id)
    assert Decimal(result["disbursed_total"]) == Decimal("3000.00")

    # Step 2: assert interim balance
    assert account_balance(acct) == Decimal("7000.00")

    # Step 3: record external payment + allocate against remaining charge
    ext_payment = Payment.objects.create(
        school_id=sid,
        account=acct,
        amount=Decimal("7000.00"),
        source="EXTERNAL",
        reference="check-001",
    )
    Allocation.objects.create(
        school_id=sid,
        payment=ext_payment,
        charge=charge,
        amount=Decimal("7000.00"),
    )

    # Step 4: assert zero balance
    final_bal = account_balance(acct)
    assert final_bal == Decimal("0.00"), f"Expected 0.00, got {final_bal}"

    # Step 5: statement sanity check
    stmt = build_account_statement(school_id=sid, account=acct)
    assert stmt["balance"] == "0.00", stmt
    assert len(stmt["entries"]) == 3, (
        f"Expected 3 entries (1 CHARGE, 2 PAYMENT_ALLOCATION), got {len(stmt['entries'])}"
    )
