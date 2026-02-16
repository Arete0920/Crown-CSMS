from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import JournalEntry, JournalLine


def post_journal_entry(
    *,
    school,
    created_by,
    lines,
    memo="",
    reference_type=None,
    reference_id=None,
):
    """
    lines = [
        {"account": GLAccount, "debit": Decimal, "credit": Decimal},
        ...
    ]
    """

    if not lines or len(lines) < 2:
        raise ValidationError("Journal entry must contain at least two lines.")

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
            locked=False,  # temporarily unlocked during creation
        )

        for line in lines:
            JournalLine.objects.create(
                entry=entry,
                account=line["account"],
                debit=line.get("debit", Decimal("0.00")),
                credit=line.get("credit", Decimal("0.00")),
            )

        # Lock entry after all lines created
        entry.locked = True
        entry.save()

    return entry
