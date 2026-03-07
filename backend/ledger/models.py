import uuid
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from households.models import Household


class ImmutableMoneyMixin:
    """
    Phase 2 Priority 5: prevent silent edits to money-critical fields after creation.

    On UPDATE (pk exists and not adding), forbids changes to fields in
    IMMUTABLE_FIELDS that actually exist on the model. Non-existent fields
    are silently skipped — no crashes on schema differences.
    """

    # Subclasses declare their own IMMUTABLE_FIELDS — base is empty.
    IMMUTABLE_FIELDS = ()

    def _immutable_check(self):
        # Only enforce on updates, not inserts.
        if not getattr(self, "pk", None):
            return
        if getattr(self, "_state", None) is not None and self._state.adding:
            return

        cls = self.__class__
        try:
            original = cls.objects.get(pk=self.pk)
        except Exception:
            # Cannot load original — do not block (avoids false negatives).
            return

        for field in self.IMMUTABLE_FIELDS:
            # is_void is explicitly excluded — it is the legitimate correction path.
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
	"""
	One ledger account per household (spine rule: keep it simple).
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	household = models.OneToOneField(Household, on_delete=models.PROTECT, related_name="ledger_account")

	class Meta:
		db_table = "ledger_account"
		indexes = [
			models.Index(fields=["school_id"]),
		]

	def __str__(self) -> str:
		return f"LedgerAccount({self.household_id})"


class Charge(ImmutableMoneyMixin, TimeStampedModel):
	IMMUTABLE_FIELDS = ("school_id", "account_id", "amount")

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="charges")

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


class Payment(ImmutableMoneyMixin, TimeStampedModel):
	IMMUTABLE_FIELDS = ("school_id", "account_id", "amount", "source", "reference")

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="payments")

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
	"""
	Minimal join: how much of a payment is applied to a charge.
	"""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="allocations")
	charge = models.ForeignKey(Charge, on_delete=models.PROTECT, related_name="allocations")

	amount = models.DecimalField(max_digits=10, decimal_places=2)

	class Meta:
		db_table = "allocation"
		constraints = [
			models.UniqueConstraint(fields=["payment", "charge"], name="uniq_payment_charge_allocation"),
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
	"""
	Spine helper: balance = total charges - total allocations applied.
	Ignores voided charges.
	"""
	charges_total = (
		account.charges.filter(is_void=False).aggregate(models.Sum("amount")).get("amount__sum")
		or Decimal("0.00")
	)
	alloc_total = (
		Allocation.objects.filter(school_id=account.school_id, charge__account=account)
		.aggregate(models.Sum("amount"))
		.get("amount__sum")
		or Decimal("0.00")
	)
	return charges_total - alloc_total

# Stage 2 — Revenue Integrity models registered under the ledger app
from .models_dunning import DunningRecord, Chargeback, DailyPayoutAudit  # noqa: E402,F401