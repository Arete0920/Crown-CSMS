import uuid
from decimal import Decimal
from django.db import models
from households.models import Household


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


class Charge(TimeStampedModel):
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


class Payment(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	school_id = models.UUIDField(db_index=True)
	account = models.ForeignKey(LedgerAccount, on_delete=models.PROTECT, related_name="payments")

	reference = models.CharField(max_length=120, blank=True, default="")
	amount = models.DecimalField(max_digits=10, decimal_places=2)

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
