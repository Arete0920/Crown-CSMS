from decimal import Decimal

from django.db import transaction

from payments.models import (
    BankStatementEntry,
    PayoutBankMatch,
    PayoutBankMatchStatus,
    ProviderPayoutBatch,
)


CENT = Decimal("0.01")


def _money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _abs_decimal(value: Decimal) -> Decimal:
    return value.copy_abs()


@transaction.atomic
def auto_match_payout_batches_for_school(*, school_id, day_window: int = 5, tolerance: Decimal = CENT) -> int:
    """
    Match ProviderPayoutBatch.net_amount to unmatched bank statement entry amounts
    within a date window and amount tolerance.

    This intentionally matches one payout batch to one bank entry.
    """
    matched_count = 0

    payout_batches = (
        ProviderPayoutBatch.objects.filter(school_id=school_id)
        .exclude(bank_matches__isnull=False)
        .order_by("-settled_at", "-id")
    )

    for payout in payout_batches:
        payout_date = payout.settled_at.date() if payout.settled_at else None
        payout_amount = _money(payout.net_amount)

        candidate = None
        best_score = None

        bank_entries = BankStatementEntry.objects.filter(school_id=school_id, is_matched=False).order_by("-posted_date", "-id")
        for entry in bank_entries:
            amount_delta = _abs_decimal(_money(entry.amount) - payout_amount)

            if amount_delta > tolerance:
                continue

            if payout_date is not None:
                date_delta_days = abs((entry.posted_date - payout_date).days)
                if date_delta_days > day_window:
                    continue
            else:
                date_delta_days = 999

            score = (date_delta_days, amount_delta)

            if best_score is None or score < best_score:
                best_score = score
                candidate = entry

        if candidate is None:
            continue

        PayoutBankMatch.objects.create(
            school_id=school_id,
            payout_batch=payout,
            bank_entry=candidate,
            status=PayoutBankMatchStatus.AUTO_MATCHED,
            amount_delta=_abs_decimal(_money(candidate.amount) - payout_amount),
            date_delta_days=best_score[0] if best_score else 0,
            note="Auto-matched by amount/date window.",
        )

        candidate.is_matched = True
        candidate.save(update_fields=["is_matched"])
        matched_count += 1

    return matched_count


@transaction.atomic
def create_manual_payout_match(*, school_id, payout_batch: ProviderPayoutBatch, bank_entry: BankStatementEntry, user=None, note: str = ""):
    if payout_batch.school_id != school_id or bank_entry.school_id != school_id:
        raise ValueError("School mismatch in manual payout match.")

    amount_delta = _abs_decimal(_money(bank_entry.amount) - _money(payout_batch.net_amount))
    date_delta_days = 0
    if payout_batch.settled_at:
        date_delta_days = abs((bank_entry.posted_date - payout_batch.settled_at.date()).days)

    match = PayoutBankMatch.objects.create(
        school_id=school_id,
        payout_batch=payout_batch,
        bank_entry=bank_entry,
        status=PayoutBankMatchStatus.MANUAL_MATCHED,
        amount_delta=amount_delta,
        date_delta_days=date_delta_days,
        note=note or "Manually matched by finance user.",
        matched_by=user,
    )

    bank_entry.is_matched = True
    bank_entry.save(update_fields=["is_matched"])

    return match
