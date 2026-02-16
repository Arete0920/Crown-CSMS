from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
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


def create_reversal_entry(*, original_entry: JournalEntry, reason: str) -> JournalEntry:
    """
    Create an immutable reversing JournalEntry for original_entry.
    Idempotent via DB: JournalEntry.reversal_of is OneToOne.
    """
    # Fast-path
    if getattr(original_entry, "reversal_entry_id", None):
        return original_entry.reversal_entry

    with transaction.atomic():
        # Lock original to prevent races
        original_entry = (
            JournalEntry.objects
            .select_for_update()
            .prefetch_related("lines")
            .get(pk=original_entry.pk)
        )

        if getattr(original_entry, "reversal_entry_id", None):
            return original_entry.reversal_entry

        # Build kwargs for reversal header (include optional fields if they exist)
        create_kwargs = {
            "school": original_entry.school,
            "created_by": original_entry.created_by,
            "reference_type": "charge_void_reversal",
            "reference_id": original_entry.reference_id,  # charge id already stored there
            "locked": True,
            "reversal_of": original_entry,
            "memo": f"REVERSAL: {reason}",
        }
        
        # Add optional fields if they exist in the model
        optional_fields = {
            "description": f"REVERSAL: {reason}",
            "entry_date": getattr(original_entry, "entry_date", None) or timezone.now().date(),
            "posted_at": getattr(original_entry, "posted_at", None),
        }
        for attr, value in optional_fields.items():
            if hasattr(JournalEntry, attr):
                create_kwargs[attr] = value
        
        # Create reversal header (all fields set during create, no update needed)
        rev = JournalEntry.objects.create(**create_kwargs)

        # Reverse every line (swap DR/CR, keep account)
        new_lines = []
        for line in original_entry.lines.all():
            new_lines.append(JournalLine(
                entry=rev,
                account=line.account,
                debit=line.credit,
                credit=line.debit,
            ))
            # Carry memo if present
            if hasattr(line, "memo") and hasattr(new_lines[-1], "memo"):
                new_lines[-1].memo = line.memo

        JournalLine.objects.bulk_create(new_lines)
        return rev
