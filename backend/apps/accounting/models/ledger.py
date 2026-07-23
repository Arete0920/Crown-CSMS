import uuid

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models


def _normalized_uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


def _require_same_tenant(instance, relation_name: str) -> None:
    relation_id = getattr(instance, f"{relation_name}_id", None)
    if relation_id is None:
        return
    try:
        related = getattr(instance, relation_name)
    except ObjectDoesNotExist as exc:
        raise ValidationError(
            {relation_name: "Related record does not exist."}
        ) from exc
    if _normalized_uuid(instance.tenant_id) != _normalized_uuid(related.tenant_id):
        raise ValidationError(
            {relation_name: "Related record must belong to the same tenant."}
        )


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

    def clean(self):
        super().clean()
        _require_same_tenant(self, "journal_entry")
        _require_same_tenant(self, "account")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Ledger entries are immutable.")
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Ledger entries cannot be deleted.")
