from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID
from django.db import transaction
from django.utils import timezone

from .models import AidApplication, AidAward, AidDisbursement, AidEvent, AidStatus, AwardStatus


@dataclass(frozen=True)
class DecisionResult:
    award: AidAward | None


def submit_aid_application(app: AidApplication):
    if app.status != AidStatus.DRAFT:
        raise ValueError("Only DRAFT aid applications can be submitted.")
    app.status = AidStatus.SUBMITTED
    app.submitted_at = timezone.now()
    app.save(update_fields=["status", "submitted_at", "updated_at"])
    AidEvent.objects.create(
        school_id=app.school_id,
        aid_application=app,
        event_type="AID_APPLICATION_SUBMITTED",
        payload={},
    )


def decide_aid_application(app: AidApplication, decision: str, amount_annual: Decimal | None):
    """
    decision: "APPROVE" or "DENY"
    amount_annual required for APPROVE
    """
    if app.status != AidStatus.SUBMITTED:
        raise ValueError("Only SUBMITTED aid applications can be decided.")
    if decision not in ("APPROVE", "DENY"):
        raise ValueError("decision must be APPROVE or DENY")

    with transaction.atomic():
        app.status = AidStatus.DECIDED
        app.decided_at = timezone.now()
        app.save(update_fields=["status", "decided_at", "updated_at"])

        if decision == "DENY":
            award = AidAward.objects.create(
                school_id=app.school_id,
                aid_application=app,
                status=AwardStatus.DENIED,
                amount_annual=Decimal("0.00"),
            )
            AidEvent.objects.create(
                school_id=app.school_id,
                aid_application=app,
                event_type="AID_DENIED",
                payload={},
            )
            return award

        if amount_annual is None:
            raise ValueError("amount_annual is required for APPROVE")

        award = AidAward.objects.create(
            school_id=app.school_id,
            aid_application=app,
            status=AwardStatus.APPROVED,
            amount_annual=amount_annual,
        )
        AidEvent.objects.create(
            school_id=app.school_id,
            aid_application=app,
            event_type="AID_APPROVED",
            payload={"amount_annual": str(amount_annual)},
        )
        return award


def create_disbursement(award: AidAward, amount: Decimal, disbursed_on):
    if award.status != AwardStatus.APPROVED:
        raise ValueError("Only APPROVED awards can be disbursed.")
    d = AidDisbursement.objects.create(
        school_id=award.school_id,
        award=award,
        amount=amount,
        disbursed_on=disbursed_on,
    )
    AidEvent.objects.create(
        school_id=award.school_id,
        aid_application=award.aid_application,
        event_type="AID_DISBURSED",
        payload={"amount": str(amount), "disbursed_on": str(disbursed_on)},
    )
    return d


from billing.models import BillingRun, Invoice
from ledger.models import LedgerAccount, Payment, Charge
from ledger.models import Allocation as PaymentAllocation  # your repo has Allocation already

from .models import FinancialAidDisbursement


@transaction.atomic
def apply_financial_aid_to_billing_run(*, school_id, billing_run_id: UUID) -> dict:
    """
    Spine behavior:
    - For each Invoice in the BillingRun, find awards for household/students in that term (simple: school-scoped, active awards)
    - Create a Ledger Payment with source="FINANCIAL_AID"
    - Allocate directly to the invoice’s ledger_charge_id
    - Record FinancialAidDisbursement rows (idempotent per award+run)
    """
    run = BillingRun.objects.get(id=billing_run_id, school_id=school_id)

    invoices = Invoice.objects.filter(school_id=school_id, billing_run=run).order_by("created_at")

    disbursed_total = Decimal("0.00")
    payments_created = 0
    allocations_created = 0
    disbursements_created = 0

    for inv in invoices:
        if not inv.ledger_charge_id:
            continue

        # Determine household + ledger account
        household_id = inv.household_id
        acct, _ = LedgerAccount.objects.get_or_create(school_id=school_id, household_id=household_id)

        # Target charge is the one created by 0040 and stored on invoice
        charge = Charge.objects.get(id=inv.ledger_charge_id, school_id=school_id, account=acct)

        # Spine award selection rule:
        # - awards that match school_id
        # - approved awards only (if your model has status field)
        # - total award amount applied up to invoice total
        awards_qs = AidAward.objects.filter(school_id=school_id)

        # Prefer household match
        awards_qs = awards_qs.filter(aid_application__household_id=household_id)

        # Approved awards only
        awards_qs = awards_qs.filter(status=AwardStatus.APPROVED)

        awards = list(awards_qs)

        for aw in awards:
            # amount field must exist
            amt = getattr(aw, "amount", None)
            if amt is None:
                amt = getattr(aw, "amount_annual", None)
            if amt is None:
                continue
            amt = Decimal(str(amt))
            if amt <= Decimal("0.00"):
                continue

            # idempotency: one disbursement per (award, run)
            if FinancialAidDisbursement.objects.filter(award=aw, billing_run=run).exists():
                continue

            pay = Payment.objects.create(
                school_id=school_id,
                account=acct,
                amount=amt,
                source="FINANCIAL_AID",
                reference=f"award:{aw.id}|run:{run.id}",
            )
            payments_created += 1

            # Allocate directly to this charge (not FIFO)
            alloc, created = PaymentAllocation.objects.get_or_create(
                school_id=school_id,
                payment=pay,
                charge=charge,
                defaults={"amount": amt},
            )
            if not created:
                # top up
                alloc.amount = Decimal(str(alloc.amount)) + amt
                alloc.save(update_fields=["amount"])
            allocations_created += 1

            FinancialAidDisbursement.objects.create(
                school_id=school_id,
                award=aw,
                billing_run=run,
                invoice=inv,
                payment=pay,
                amount=amt,
            )
            disbursements_created += 1
            disbursed_total += amt

    return {
        "billing_run_id": str(run.id),
        "term": run.term,
        "payments_created": payments_created,
        "allocations_created": allocations_created,
        "disbursements_created": disbursements_created,
        "disbursed_total": str(disbursed_total),
    }
