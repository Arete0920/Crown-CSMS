import uuid

from django.core.exceptions import ValidationError
from django.db import models


class LedgerAccount(models.Model):

    ACCOUNT_TYPES = [
        ("ASSET", "Asset"),
        ("LIABILITY", "Liability"),
        ("EQUITY", "Equity"),
        ("REVENUE", "Revenue"),
        ("EXPENSE", "Expense"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant_id = models.UUIDField(db_index=True)

    code = models.CharField(max_length=20)

    name = models.CharField(max_length=255)

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant_id", "code")

    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant_id = models.UUIDField(db_index=True)

    correlation_id = models.UUIDField(db_index=True)

    source_system = models.CharField(max_length=100)

    created_by = models.UUIDField()

    description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    is_reversal = models.BooleanField(default=False)

    reversal_of = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    class Meta:
        ordering = ["-created_at"]


class LedgerEntry(models.Model):

    ENTRY_TYPES = [
        ("DEBIT", "Debit"),
        ("CREDIT", "Credit"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tenant_id = models.UUIDField(db_index=True)

    journal_entry = models.ForeignKey(
        JournalEntry,
        related_name="entries",
        on_delete=models.PROTECT,
    )

    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.PROTECT,
    )

    entry_type = models.CharField(
        max_length=10,
        choices=ENTRY_TYPES,
    )

    amount = models.DecimalField(
        max_digits=18,
        decimal_places=2,
    )

    currency = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise ValidationError(
                "Ledger entries are immutable."
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(
            "Ledger entries cannot be deleted."
        )
