from collections import defaultdict
from decimal import Decimal

from django.db import transaction

from payments.models import (
    BankStatementEntry,
    PayoutBankMatch,
    PayoutBankMatchStatus,
    ProviderPayoutBatch,
)


CENT = Decimal("0.01")
ACTIVE_MATCH_STATUSES = (
    PayoutBankMatchStatus.AUTO_MATCHED,
    PayoutBankMatchStatus.MANUAL_MATCHED,
)
AUTO_MATCH_RULE = "amount_currency_settled_date_v1"
MANUAL_MATCH_RULE = "manual_finance_user_v1"


def _money(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _abs_decimal(value: Decimal) -> Decimal:
    return value.copy_abs()


def _currency(value: str) -> str:
    return (value or "USD").strip().upper()


def _match_note(*, rule: str, payout: ProviderPayoutBatch, bank_entry: BankStatementEntry, tolerance: Decimal | None = None, day_window: int | None = None) -> str:
    parts = [
        f"rule={rule}",
        f"provider={payout.provider}",
        f"payout_id={payout.payout_id}",
        f"payout_currency={_currency(payout.currency)}",
        f"bank_reference={bank_entry.reference or '-'}",
        f"bank_currency={_currency(bank_entry.currency)}",
    ]
    if tolerance is not None:
        parts.append(f"tolerance={tolerance}")
    if day_window is not None:
        parts.append(f"day_window={day_window}")
    return "; ".join(parts)


def _candidate_score(*, payout: ProviderPayoutBatch, entry: BankStatementEntry, tolerance: Decimal, day_window: int):
    if payout.settled_at is None:
        return None
    if _currency(entry.currency) != _currency(payout.currency):
        return None

    amount_delta = _abs_decimal(_money(entry.amount) - _money(payout.net_amount))
    if amount_delta > tolerance:
        return None

    date_delta_days = abs((entry.posted_date - payout.settled_at.date()).days)
    if date_delta_days > day_window:
        return None

    return (date_delta_days, amount_delta)


@transaction.atomic
def auto_match_payout_batches_for_school(*, school_id, day_window: int = 5, tolerance: Decimal = CENT) -> int:
    """
    Conservatively match payout batches to bank entries using external evidence.

    Auto-match requires:
    - a provider settlement timestamp,
    - same currency,
    - amount/date tolerance compliance,
    - one unique best bank candidate for the payout, and
    - no competing payout that could claim that bank entry.

    Ambiguous or incomplete evidence remains unmatched for manual review.
    """
    day_window = int(day_window)
    tolerance = _money(tolerance)
    if day_window < 0:
        raise ValueError("day_window cannot be negative.")
    if tolerance < Decimal("0.00"):
        raise ValueError("tolerance cannot be negative.")

    payout_batches = list(
        ProviderPayoutBatch.objects.select_for_update()
        .filter(school_id=school_id)
        .exclude(bank_matches__status__in=ACTIVE_MATCH_STATUSES)
        .order_by("-settled_at", "-id")
        .distinct()
    )
    bank_entries = list(
        BankStatementEntry.objects.select_for_update()
        .select_related("statement_import")
        .filter(school_id=school_id, is_matched=False)
        .exclude(payout_matches__status__in=ACTIVE_MATCH_STATUSES)
        .order_by("-posted_date", "-id")
        .distinct()
    )

    candidates_by_payout: dict[int, list[tuple[tuple[int, Decimal], BankStatementEntry]]] = defaultdict(list)
    payout_candidates_by_bank: dict[int, set[int]] = defaultdict(set)

    for payout in payout_batches:
        if payout.settled_at is None:
            continue
        for entry in bank_entries:
            score = _candidate_score(
                payout=payout,
                entry=entry,
                tolerance=tolerance,
                day_window=day_window,
            )
            if score is None:
                continue
            candidates_by_payout[payout.pk].append((score, entry))
            payout_candidates_by_bank[entry.pk].add(payout.pk)

    matched_count = 0
    claimed_bank_ids: set[int] = set()

    for payout in payout_batches:
        candidates = candidates_by_payout.get(payout.pk, [])
        if not candidates:
            continue

        best_score = min(score for score, _entry in candidates)
        best_candidates = [entry for score, entry in candidates if score == best_score]
        if len(best_candidates) != 1:
            continue

        candidate = best_candidates[0]
        if candidate.pk in claimed_bank_ids:
            continue
        if len(payout_candidates_by_bank[candidate.pk]) != 1:
            continue

        PayoutBankMatch.objects.create(
            school_id=school_id,
            payout_batch=payout,
            bank_entry=candidate,
            status=PayoutBankMatchStatus.AUTO_MATCHED,
            amount_delta=best_score[1],
            date_delta_days=best_score[0],
            note=_match_note(
                rule=AUTO_MATCH_RULE,
                payout=payout,
                bank_entry=candidate,
                tolerance=tolerance,
                day_window=day_window,
            ),
        )

        candidate.is_matched = True
        candidate.save(update_fields=["is_matched"])
        claimed_bank_ids.add(candidate.pk)
        matched_count += 1

    return matched_count


@transaction.atomic
def create_manual_payout_match(*, school_id, payout_batch: ProviderPayoutBatch, bank_entry: BankStatementEntry, user=None, note: str = ""):
    if user is None:
        raise ValueError("Manual payout match requires an authenticated finance user.")

    payout_batch = ProviderPayoutBatch.objects.select_for_update().filter(
        pk=payout_batch.pk,
        school_id=school_id,
    ).first()
    bank_entry = (
        BankStatementEntry.objects.select_for_update()
        .select_related("statement_import")
        .filter(pk=bank_entry.pk, school_id=school_id)
        .first()
    )
    if payout_batch is None or bank_entry is None:
        raise ValueError("School mismatch in manual payout match.")

    existing_pair = PayoutBankMatch.objects.filter(
        school_id=school_id,
        payout_batch=payout_batch,
        bank_entry=bank_entry,
        status__in=ACTIVE_MATCH_STATUSES,
    ).first()
    if existing_pair is not None:
        return existing_pair

    if PayoutBankMatch.objects.filter(
        school_id=school_id,
        payout_batch=payout_batch,
        status__in=ACTIVE_MATCH_STATUSES,
    ).exists():
        raise ValueError("Payout batch is already actively matched.")
    if bank_entry.is_matched or PayoutBankMatch.objects.filter(
        school_id=school_id,
        bank_entry=bank_entry,
        status__in=ACTIVE_MATCH_STATUSES,
    ).exists():
        raise ValueError("Bank statement entry is already actively matched.")
    if payout_batch.settled_at is None:
        raise ValueError("Manual payout match requires provider settlement date evidence.")
    if _currency(bank_entry.currency) != _currency(payout_batch.currency):
        raise ValueError("Manual payout match currency must match payout currency.")

    amount_delta = _abs_decimal(_money(bank_entry.amount) - _money(payout_batch.net_amount))
    date_delta_days = abs((bank_entry.posted_date - payout_batch.settled_at.date()).days)

    provenance = _match_note(
        rule=MANUAL_MATCH_RULE,
        payout=payout_batch,
        bank_entry=bank_entry,
    )
    match = PayoutBankMatch.objects.create(
        school_id=school_id,
        payout_batch=payout_batch,
        bank_entry=bank_entry,
        status=PayoutBankMatchStatus.MANUAL_MATCHED,
        amount_delta=amount_delta,
        date_delta_days=date_delta_days,
        note=f"{provenance}; user_note={note.strip() or '-'}",
        matched_by=user,
    )

    bank_entry.is_matched = True
    bank_entry.save(update_fields=["is_matched"])

    return match