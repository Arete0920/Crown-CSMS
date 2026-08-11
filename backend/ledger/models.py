import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from households.models import Household


class ImmutableMoneyMixin:
    """Prevent silent edits to money-critical fields after creation."""

    IMMUTABLE_FIELDS = ()

    def _immutable_check(self):
        if not getattr(self, "pk", None):
            return
        if getattr(self, "_state", None) is not None and self._state.adding:
            return

        cls = self.__class__
        try:
            original = cls.objects.get(pk=self.pk)
        except Exception:
            return

        for field in self.IMMUTABLE_FIELDS:
            if field == "is_void":
                continue
            if hasattr(self, field) and hasattr(original, field):
                if getattr(self, field) != getattr(original, field):
                    raise ValidationError({field: "This field is immutable after creation."})

    def save(self, *args, **kwargs):
        self._immutable_check()
        return super().save(*args, **kwargs)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class LedgerAccount(TimeStampedModel):
    """One Student Accounts ledger account per household."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    household = models.OneToOneField(
        Household,
        on_delete=models.PROTECT,
        related_name="ledger_account",
    )

    class Meta:
        db_table = "ledger_account"
        indexes = [models.Index(fields=["school_id"])]

    def __str__(self) -> str:
        return f"LedgerAccount({self.household_id})"


class Charge(ImmutableMoneyMixin, TimeStampedModel):
    IMMUTABLE_FIELDS = ("school_id", "account_id", "amount")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.PROTECT,
        related_name="charges",
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_void = models.BooleanField(default=False)

    class Meta:
        db_table = "charge"
        indexes = [
            models.Index(fields=["school_id", "account"]),
            models.Index(fields=["school_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Charge({self.amount})"


class Credit(ImmutableMoneyMixin, TimeStampedModel):
    """
    Non-cash Student Accounts credit.

    Credits reduce household receivables but are intentionally distinct from
    Payment so financial aid, adjustments, and other non-cash reductions never
    masquerade as external money movement.
    """

    IMMUTABLE_FIELDS = ("school_id", "account_id", "source", "reference", "amount")

    SOURCE_FINANCIAL_AID = "FINANCIAL_AID"
    SOURCE_ADJUSTMENT = "ADJUSTMENT"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.PROTECT,
        related_name="credits",
    )
    source = models.CharField(max_length=32, db_index=True)
    reference = models.CharField(max_length=128, db_index=True)
    description = models.CharField(max_length=200, blank=True, default="")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_void = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "student_account_credit"
        constraints = [
            models.UniqueConstraint(
                fields=["school_id", "source", "reference"],
                name="uniq_student_account_credit_source_reference",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__gt=0),
                name="student_account_credit_amount_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["school_id", "account"],
                name="ledger_cred_school__c5bc72_idx",
            ),
            models.Index(
                fields=["school_id", "source"],
                name="ledger_cred_school__8a7f93_idx",
            ),
            models.Index(
                fields=["school_id", "created_at"],
                name="ledger_cred_school__4fbdcc_idx",
            ),
        ]

    def clean(self):
        if self.account_id and self.account.school_id != self.school_id:
            raise ValidationError({"account": "Credit account must belong to the same school."})
        if self.amount is None or self.amount <= Decimal("0.00"):
            raise ValidationError({"amount": "Credit amount must be greater than zero."})
        if not (self.reference or "").strip():
            raise ValidationError({"reference": "Credit reference is required."})

    def save(self, *args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Credits cannot be deleted. Void the credit instead.")

    def __str__(self) -> str:
        return f"Credit({self.source}, {self.amount})"


class Payment(ImmutableMoneyMixin, TimeStampedModel):
    IMMUTABLE_FIELDS = ("school_id", "account_id", "amount", "source", "reference")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    account = models.ForeignKey(
        LedgerAccount,
        on_delete=models.PROTECT,
        related_name="payments",
    )
    source = models.CharField(max_length=32, default="EXTERNAL", db_index=True)
    reference = models.CharField(max_length=64, blank=True, default="", db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_void = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "payment"
        indexes = [
            models.Index(fields=["school_id", "account"]),
            models.Index(fields=["school_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"Payment({self.amount})"


class Allocation(TimeStampedModel):
    """How much of a cash payment is applied to a charge."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    charge = models.ForeignKey(
        Charge,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "allocation"
        constraints = [
            models.UniqueConstraint(
                fields=["payment", "charge"],
                name="uniq_payment_charge_allocation",
            ),
        ]
        indexes = [
            models.Index(fields=["school_id", "payment"]),
            models.Index(fields=["school_id", "charge"]),
        ]

    def __str__(self) -> str:
        return f"Allocation({self.amount})"


class PaymentAllocation(Allocation):
    class Meta:
        proxy = True


def compute_account_balance(account: LedgerAccount) -> Decimal:
    """Canonical Student Accounts balance: charges - cash allocations - credits."""
    charges_total = (
        account.charges.filter(is_void=False).aggregate(models.Sum("amount")).get("amount__sum")
        or Decimal("0.00")
    )
    alloc_total = (
        Allocation.objects.filter(
            school_id=account.school_id,
            charge__account=account,
            charge__is_void=False,
            payment__is_void=False,
        )
        .aggregate(models.Sum("amount"))
        .get("amount__sum")
        or Decimal("0.00")
    )
    credit_total = (
        account.credits.filter(is_void=False).aggregate(models.Sum("amount")).get("amount__sum")
        or Decimal("0.00")
    )
    return charges_total - alloc_total - credit_total


from .models_dunning import DunningRecord, Chargeback, DailyPayoutAudit  # noqa: E402,F401
