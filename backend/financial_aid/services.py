from __future__ import annotations

from decimal import Decimal
from uuid import UUID
from django.db import transaction

from .models import AidAward, AidAuditEvent
from billing.models import BillingRun, Invoice
from ledger.models import LedgerAccount, Payment, Charge
from ledger.models import Allocation as PaymentAllocation

_DISBURSE_EVENT = "DISBURSED_TO_BILLING_RUN"
_ENTITY_TYPE = "AID_AWARD"


def _already_disbursed(*, school_id, award_id, billing_run_id) -> bool:
    """
    Idempotency guard: one Payment per (award, billing_run) pair.
    Stored as an AidAuditEvent with event_type=DISBURSED_TO_BILLING_RUN,
    entity_type=AID_AWARD, entity_id=award.id, message=str(billing_run_id).
    """
    return AidAuditEvent.objects.filter(
        school_id=school_id,
        event_type=_DISBURSE_EVENT,
        entity_type=_ENTITY_TYPE,
        entity_id=award_id,
        message=str(billing_run_id),
    ).exists()


@transaction.atomic
def apply_financial_aid_to_billing_run(*, school_id, billing_run_id: UUID) -> dict:
    """
    For each Invoice in the BillingRun that has a ledger_charge_id:
      - Find AidAwards for that household (school-scoped).
      - Create a Ledger Payment(source='FINANCIAL_AID') per award.
      - Allocate directly to the invoice's Charge (not FIFO).
      - Record an AidAuditEvent for idempotency (one per award+run pair).

    Calling this function twice with the same arguments is safe: awards
    already disbursed to this billing run are silently skipped.
    """
    run = BillingRun.objects.get(pk=billing_run_id, school_id=school_id)
    invoices = (
        Invoice.objects.filter(school_id=school_id, billing_run=run)
        .order_by("created_at")
    )

    disbursed_total = Decimal("0.00")
    payments_created = 0
    allocations_created = 0
    events_created = 0

    for inv in invoices:
        if not inv.ledger_charge_id:
            continue

        household_id = inv.household_id
        acct, _ = LedgerAccount.objects.get_or_create(
            school_id=school_id,
            household_id=household_id,
        )

        try:
            charge = Charge.objects.get(
                id=inv.ledger_charge_id,
                school_id=school_id,
                account=acct,
            )
        except Charge.DoesNotExist:
            continue

        awards = list(
            AidAward.objects.filter(
                school_id=school_id,
                application__household_id=household_id,
            )
        )

        for aw in awards:
            amt = Decimal(str(aw.amount))
            if amt <= Decimal("0.00"):
                continue

            if _already_disbursed(
                school_id=school_id,
                award_id=aw.id,
                billing_run_id=run.id,
            ):
                continue

            pay = Payment.objects.create(
                school_id=school_id,
                account=acct,
                amount=amt,
                source="FINANCIAL_AID",
                reference=f"award:{aw.id}|run:{run.id}",
            )
            payments_created += 1

            alloc, created = PaymentAllocation.objects.get_or_create(
                school_id=school_id,
                payment=pay,
                charge=charge,
                defaults={"amount": amt},
            )
            if not created:
                alloc.amount = Decimal(str(alloc.amount)) + amt
                alloc.save(update_fields=["amount"])
            allocations_created += 1

            AidAuditEvent.objects.create(
                school_id=school_id,
                event_type=_DISBURSE_EVENT,
                entity_type=_ENTITY_TYPE,
                entity_id=aw.id,
                message=str(run.id),
            )
            events_created += 1
            disbursed_total += amt

    return {
        "billing_run_id": str(run.id),
        "term": run.term,
        "payments_created": payments_created,
        "allocations_created": allocations_created,
        "events_created": events_created,
        "disbursed_total": str(disbursed_total),
    }
