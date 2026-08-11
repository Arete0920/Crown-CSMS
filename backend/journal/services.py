from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import JournalEntry, JournalLine


def _normalize_currency(currency: str) -> str:
    value = (currency or "").strip().upper()
    if not value or len(value) > 8:
        raise ValidationError("currency must be a non-empty code of at most 8 characters.")
    return value


def _normalize_source_system(source_system: str) -> str:
    value = (source_system or "").strip()
    if not value or len(value) > 100:
        raise ValidationError("source_system must be a non-empty value of at most 100 characters.")
    return value


def post_journal_entry(
    *,
    school,
    created_by,
    lines,
    memo="",
    reference_type=None,
    reference_id=None,
    correlation_id=None,
    source_system="journal",
    currency="USD",
):
    """
    Post one balanced immutable journal entry.

    lines = [
        {"account": GLAccount, "debit": Decimal, "credit": Decimal},
        ...
    ]

    correlation_id, source_system, and currency provide the canonical
    cross-domain accounting traceability contract while remaining optional for
    compatibility callers.
    """
    if not lines or len(lines) < 2:
        raise ValidationError("Journal entry must contain at least two lines.")

    source_system = _normalize_source_system(source_system)
    currency = _normalize_currency(currency)

    total_debit = Decimal("0.00")
    total_credit = Decimal("0.00")

    for line in lines:
        debit = line.get("debit", Decimal("0.00"))
        credit = line.get("credit", Decimal("0.00"))
        account = line.get("account")

        if debit < 0 or credit < 0:
            raise ValidationError("Debit and credit must be non-negative.")

        if debit > 0 and credit > 0:
            raise ValidationError("Line cannot have both debit and credit.")

        if debit == 0 and credit == 0:
            raise ValidationError("Line must have either debit or credit.")

        if account.school_id != school.id:
            raise ValidationError("Account school must match entry school.")

        total_debit += debit
        total_credit += credit

    if total_debit != total_credit:
        raise ValidationError("Journal entry must balance.")

    with transaction.atomic():
        entry = JournalEntry.objects.create(
            school=school,
            created_by=created_by,
            memo=memo,
            reference_type=reference_type,
            reference_id=reference_id,
            correlation_id=correlation_id,
            source_system=source_system,
            currency=currency,
            locked=False,
        )

        for line in lines:
            JournalLine.objects.create(
                entry=entry,
                account=line["account"],
                debit=line.get("debit", Decimal("0.00")),
                credit=line.get("credit", Decimal("0.00")),
            )

        entry.locked = True
        entry.save()

    return entry


def _find_reversal(original_entry: JournalEntry) -> JournalEntry | None:
    """Return the existing reversal without relying on a reverse ``*_id`` accessor."""
    return JournalEntry.objects.filter(reversal_of=original_entry).first()


def create_reversal_entry(*, original_entry: JournalEntry, reason: str) -> JournalEntry:
    """
    Create an immutable reversing JournalEntry for original_entry.

    Idempotency is enforced by querying the actual ``reversal_of`` relation and
    by the database OneToOne constraint. The previous reverse ``reversal_entry_id``
    lookup was not a reliable accessor for this relationship.
    """
    existing = _find_reversal(original_entry)
    if existing is not None:
        return existing

    with transaction.atomic():
        original_entry = (
            JournalEntry.objects
            .select_for_update()
            .prefetch_related("lines")
            .get(pk=original_entry.pk)
        )

        existing = _find_reversal(original_entry)
        if existing is not None:
            return existing

        base_reference_type = (original_entry.reference_type or "journal").strip() or "journal"
        reversal_reference_type = f"{base_reference_type}_reversal"[:64]

        rev = JournalEntry.objects.create(
            school=original_entry.school,
            created_by=original_entry.created_by,
            reference_type=reversal_reference_type,
            reference_id=original_entry.reference_id,
            correlation_id=original_entry.correlation_id,
            source_system=original_entry.source_system,
            currency=original_entry.currency,
            locked=True,
            reversal_of=original_entry,
            memo=f"REVERSAL: {reason}",
        )

        new_lines = [
            JournalLine(
                entry=rev,
                account=line.account,
                debit=line.credit,
                credit=line.debit,
            )
            for line in original_entry.lines.all()
        ]
        JournalLine.objects.bulk_create(new_lines)
        return rev
