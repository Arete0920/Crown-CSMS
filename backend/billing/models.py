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

	# ledger charge created for this invoice (spine: optional link as UUID)
	ledger_charge_id = models.UUIDField(null=True, blank=True)

	class Meta:
		db_table = "invoice"
		indexes = [
			models.Index(fields=["school_id", "billing_run"]),
			models.Index(fields=["school_id", "household"]),
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
