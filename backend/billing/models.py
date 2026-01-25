import uuid
from decimal import Decimal
from django.db import models

from households.models import Household, Student


class TimeStampedModel(models.Model):
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		abstract = True


class BillingRun(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)

	# e.g., "2026-FALL"
	term = models.CharField(max_length=24, db_index=True)

	# "TUITION", "ENROLLMENT_FEE", etc. (spine: just a string)
	run_type = models.CharField(max_length=32, default="TUITION", db_index=True)

	# informational
	description = models.CharField(max_length=200, default="Tuition Billing Run")

	# pricing input for spine: per-student amount (no rate tables yet)
	amount_per_student = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

	class Meta:
		db_table = "billing_run"
		indexes = [
			models.Index(fields=["school_id", "term"]),
			models.Index(fields=["school_id", "run_type"]),
		]

	def __str__(self) -> str:
		return f"BillingRun({self.term}, {self.run_type})"


class Invoice(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)

	billing_run = models.ForeignKey(BillingRun, on_delete=models.CASCADE, related_name="invoices")
	household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="invoices")

	total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

	# Installments: optional due date for this invoice
	due_on = models.DateField(null=True, blank=True, db_index=True)

	# ledger charge created for this invoice (spine: optional link as UUID)
	ledger_charge_id = models.UUIDField(null=True, blank=True)

	class Meta:
		db_table = "invoice"
		indexes = [
			models.Index(fields=["school_id", "billing_run"]),
			models.Index(fields=["school_id", "household"]),
			models.Index(fields=["school_id", "due_on"]),
		]

	def __str__(self) -> str:
		return f"Invoice({self.household_id}, {self.total_amount})"


class InvoiceLine(TimeStampedModel):
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)

	invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
	student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="invoice_lines")

	description = models.CharField(max_length=200, default="Tuition")
	amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

	class Meta:
		db_table = "invoice_line"
		indexes = [
			models.Index(fields=["school_id", "invoice"]),
			models.Index(fields=["school_id", "student"]),
		]

	def __str__(self) -> str:
		return f"InvoiceLine({self.student_id}, {self.amount})"


class InstallmentPlan(TimeStampedModel):
	"""Installment template for a term."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)

	term = models.CharField(max_length=24, db_index=True)
	name = models.CharField(max_length=120, db_index=True)

	installment_count = models.PositiveIntegerField(default=1)
	first_due_on = models.DateField()
	cadence_days = models.PositiveIntegerField(default=30)

	class Meta:
		db_table = "installment_plan"
		indexes = [
			models.Index(fields=["school_id", "term"]),
			models.Index(fields=["school_id", "name"]),
		]

	def __str__(self) -> str:
		return f"InstallmentPlan({self.term}, {self.name})"


class InstallmentScheduleItem(TimeStampedModel):
	"""Generated schedule item for a household under a plan."""
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)

	plan = models.ForeignKey(InstallmentPlan, on_delete=models.CASCADE, related_name="items")
	household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="installment_schedule_items")

	sequence = models.PositiveIntegerField()
	due_on = models.DateField(db_index=True)
	amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

	invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL, related_name="installment_items")

	class Meta:
		db_table = "installment_schedule_item"
		constraints = [
			models.UniqueConstraint(fields=["plan", "household", "sequence"], name="uniq_plan_household_sequence"),
		]
		indexes = [
			models.Index(fields=["school_id", "plan"]),
			models.Index(fields=["school_id", "household"]),
			models.Index(fields=["school_id", "due_on"]),
		]

	def __str__(self) -> str:
		return f"InstallmentScheduleItem({self.household_id}, {self.due_on}, {self.amount})"
