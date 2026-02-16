from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.conf import settings
from decimal import Decimal


class GLAccount(models.Model):
    """
    Chart of Accounts - General Ledger account definitions.
    Tenant-scoped, hierarchical structure.
    """
    ACCOUNT_TYPES = [
        ("ASSET", "Asset"),
        ("LIABILITY", "Liability"),
        ("EQUITY", "Equity"),
        ("REVENUE", "Revenue"),
        ("EXPENSE", "Expense"),
    ]

    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="gl_accounts",
    )

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    account_type = models.CharField(max_length=16, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "journal_gl_account"
        unique_together = ("school", "code")
        indexes = [models.Index(fields=["school", "code"])]

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """
    Immutable journal entry - header for double-entry transactions.
    Once locked (default), cannot be modified or deleted.
    """
    school = models.ForeignKey(
        "core.School",
        on_delete=models.PROTECT,
        related_name="journal_entries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="journal_entries",
    )

    memo = models.TextField(blank=True)
    locked = models.BooleanField(default=True)

    reference_type = models.CharField(max_length=64, blank=True, null=True)
    reference_id = models.UUIDField(blank=True, null=True)

    class Meta:
        db_table = "journal_entry"
        indexes = [
            models.Index(fields=["school", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def clean(self):
        if self.pk and self.locked:
            raise ValidationError("Locked journal entries cannot be modified.")

    def save(self, *args, **kwargs):
        if self.pk:
            original = JournalEntry.objects.get(pk=self.pk)
            if original.locked:
                raise ValidationError("Locked journal entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Journal entries cannot be deleted.")

    def __str__(self):
        return f"Entry {self.id} - {self.memo}"


class JournalLine(models.Model):
    """
    Individual debit/credit line in a journal entry.
    Enforces debit XOR credit (not both, not neither).
    Cannot be modified after entry is locked.
    """
    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name="lines",
    )

    account = models.ForeignKey(
        GLAccount,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )

    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        db_table = "journal_line"
        indexes = [
            models.Index(fields=["entry", "account"]),
        ]

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("Debit and credit must be non-negative.")

        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Line cannot have both debit and credit.")

        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Line must have either debit or credit.")

        if self.account.school_id != self.entry.school_id:
            raise ValidationError("Account school must match entry school.")

    def save(self, *args, **kwargs):
        if self.entry.locked:
            raise ValidationError("Cannot modify lines of a locked entry.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Journal lines cannot be deleted.")

    def __str__(self):
        if self.debit > 0:
            return f"DR {self.account.code}: {self.debit}"
        return f"CR {self.account.code}: {self.credit}"
