from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import AccountingPeriod, JournalEntry, JournalLine


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


def _effective_posting_date(value: date | None) -> date:
    return value or timezone.localdate()


def assert_posting_period_open(*, school, posting_date: date) -> AccountingPeriod | None:
    """
    Fail closed when an explicitly configured period covering posting_date is closed.

    Existing schools without configured periods remain backward-compatible until
    Finance administrators establish their period calendar.
    """
    period = AccountingPeriod.objects.filter(
        school=school,
        start_date__lte=posting_date,
        end_date__gte=posting_date,
    ).first()
    if period is not None and period.status == AccountingPeriod.Status.CLOSED:
        raise ValidationError(
            f"Accounting period {period.start_date} through {period.end_date} is closed."
        )
    return period


def close_accounting_period(*, period: AccountingPeriod, user, note="") -> AccountingPeriod:
    """Close a posting period under row lock so concurrent posting cannot race closure."""
    with transaction.atomic():
        period = AccountingPeriod.objects.select_for_update().get(pk=period.pk)
        return period.close(user=user, note=note)


def reopen_accounting_period(*, period: AccountingPeriod, user, reason: str) -> AccountingPeriod:
    """Reopen a period with an explicit reason and durable actor/timestamp evidence."""
    with transaction.atomic():
        period = AccountingPeriod.objects.select_for_update().get(pk=period.pk)
        return period.reopen(user=user, reason=reason)


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
    posting_date=None,
):
    """
    Post one balanced immutable journal entry.

    lines = [
        {"account": GLAccount, "debit": Decimal, "credit": Decimal},
        ...
    ]

    correlation_id, source_system, currency, and posting_date provide the
    canonical cross-domain accounting traceability contract while remaining
    compatible with callers that omit the newer metadata.
    """
    if not lines or len(lines) < 2:
        raise ValidationError("Journal entry must contain at least two lines.")

    source_system = _normalize_source_system(source_system)
    currency = _normalize_currency(currency)
    posting_date = _effective_posting_date(posting_date)
    assert_posting_period_open(school=school, posting_date=posting_date)

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
        # Recheck under a transaction so period closure and posting have a
        # deterministic ordering when they contend.
        period = AccountingPeriod.objects.select_for_update().filter(
            school=school,
            start_date__lte=posting_date,
            end_date__gte=posting_date,
        ).first()
        if period is not None and period.status == AccountingPeriod.Status.CLOSED:
            raise ValidationError(
                f"Accounting period {period.start_date} through {period.end_date} is closed."
            )

        entry = JournalEntry.objects.create(
            school=school,
            created_by=created_by,
            posting_date=posting_date,
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
                fund_code=line.get("fund_code", ""),
                department_code=line.get("department_code", ""),
                program_code=line.get("program_code", ""),
                campus_code=line.get("campus_code", ""),
                project_code=line.get("project_code", ""),
            )

        entry.locked = True
        entry.save()

    return entry


def _find_reversal(original_entry: JournalEntry) -> JournalEntry | None:
    """Return the existing reversal without relying on a reverse ``*_id`` accessor."""
    return JournalEntry.objects.filter(reversal_of=original_entry).first()


def create_reversal_entry(
    *,
    original_entry: JournalEntry,
    reason: str,
    reference_type: str | None = None,
    posting_date=None,
) -> JournalEntry:
    """
    Create one immutable reversing JournalEntry for ``original_entry``.

    Reversals post on the requested/current posting date, not automatically into
    the original period. This allows prior periods to remain closed while still
    supporting controlled corrections in the current open period.
    """
    existing = _find_reversal(original_entry)
    if existing is not None:
        return existing

    posting_date = _effective_posting_date(posting_date)

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

        assert_posting_period_open(
            school=original_entry.school,
            posting_date=posting_date,
        )

        base_reference_type = (original_entry.reference_type or "journal").strip() or "journal"
        reversal_reference_type = (reference_type or f"{base_reference_type}_reversal").strip()
        if not reversal_reference_type or len(reversal_reference_type) > 64:
            raise ValidationError("reversal reference_type must be between 1 and 64 characters.")

        rev = JournalEntry.objects.create(
            school=original_entry.school,
            created_by=original_entry.created_by,
            posting_date=posting_date,
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
                fund_code=line.fund_code,
                department_code=line.department_code,
                program_code=line.program_code,
                campus_code=line.campus_code,
                project_code=line.project_code,
            )
            for line in original_entry.lines.all()
        ]
        JournalLine.objects.bulk_create(new_lines)
        return rev
