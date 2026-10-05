import uuid
from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from households.models import Guardian, Household, Student


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


class BillingAuditEvent(TimeStampedModel):
	ENTITY_INVOICE = "INVOICE"
	ENTITY_PAYMENT = "PAYMENT"

	school_id = models.UUIDField(db_index=True)
	entity_type = models.CharField(max_length=24)
	entity_id = models.UUIDField()
	action = models.CharField(max_length=64)
	actor_user = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.PROTECT,
		null=True,
		blank=True,
		related_name="billing_audit_events",
	)

	timestamp = models.DateTimeField(default=timezone.now)
	details_json = models.JSONField(default=dict, blank=True)

	class Meta:
		indexes = [
			models.Index(fields=["school_id", "entity_type", "entity_id"]),
			models.Index(fields=["school_id", "timestamp"]),
			models.Index(fields=["school_id", "action"]),
		]

	def __str__(self) -> str:
		return f"{self.timestamp} — {self.entity_type}:{self.entity_id} — {self.action}"

	@staticmethod
	def log(
		school_id,
		entity_type: str,
		entity_id,
		action: str,
		actor_user=None,
		details: dict | None = None,
	):
		return BillingAuditEvent.objects.create(
			school_id=school_id,
			entity_type=entity_type,
			entity_id=entity_id,
			action=action,
			actor_user=actor_user,
			timestamp=timezone.now(),
			details_json=details or {},
		)

# Stage 2 — Revenue Integrity models registered under the billing app
from .models_delinquency import HouseholdDelinquency  # noqa: E402,F401

class BillingPayer(TimeStampedModel):
	"""A person or organization responsible for a defined share of a household bill."""

	class PayerType(models.TextChoices):
		GUARDIAN = "GUARDIAN", "Guardian"
		THIRD_PARTY = "THIRD_PARTY", "Third party"
		ORGANIZATION = "ORGANIZATION", "Organization"

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)
	household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="billing_payers")
	guardian = models.ForeignKey(
		Guardian,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name="billing_payer_profiles",
	)
	account = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name="billing_payer_profiles",
	)
	payer_type = models.CharField(max_length=20, choices=PayerType.choices, default=PayerType.GUARDIAN)
	display_name = models.CharField(max_length=160, blank=True, default="")
	email = models.EmailField(blank=True, default="")
	is_active = models.BooleanField(default=True, db_index=True)

	class Meta:
		db_table = "billing_payer"
		indexes = [
			models.Index(fields=["school_id", "household", "is_active"], name="billing_pay_school__d32d57_idx"),
			models.Index(fields=["school_id", "account", "is_active"], name="billing_pay_school__b09b75_idx"),
		]
		constraints = [
			models.UniqueConstraint(
				fields=["school_id", "household", "guardian"],
				name="uniq_billing_payer_household_guardian",
			),
		]

	def clean(self):
		if self.household_id and self.school_id != self.household.school_id:
			raise ValidationError({"household": "Household must belong to the same school."})
		if self.guardian_id:
			if self.school_id != self.guardian.school_id:
				raise ValidationError({"guardian": "Guardian must belong to the same school."})
			if self.household_id != self.guardian.household_id:
				raise ValidationError({"guardian": "Guardian must belong to the payer household."})
			if self.account_id and self.guardian.account_id and self.account_id != self.guardian.account_id:
				raise ValidationError({"account": "Guardian payer account must match the guardian account."})
		if self.payer_type == self.PayerType.GUARDIAN and not self.guardian_id:
			raise ValidationError({"guardian": "Guardian payer type requires a guardian."})
		account_school_id = getattr(self.account, "school_id", None) if self.account_id else None
		if account_school_id and self.school_id != account_school_id:
			raise ValidationError({"account": "Payer account must belong to the same school."})
		if not self.guardian_id and not self.display_name.strip():
			raise ValidationError({"display_name": "Non-guardian payers require a display name."})

	def __str__(self) -> str:
		if self.display_name:
			return self.display_name
		if self.guardian_id:
			return str(self.guardian)
		return str(self.id)


class BillingResponsibilityRule(TimeStampedModel):
	"""Percentage responsibility for a charge type, optionally scoped to one student."""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)
	household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="billing_responsibility_rules")
	payer = models.ForeignKey(BillingPayer, on_delete=models.PROTECT, related_name="responsibility_rules")
	student = models.ForeignKey(
		Student,
		null=True,
		blank=True,
		on_delete=models.PROTECT,
		related_name="billing_responsibility_rules",
	)
	charge_type = models.CharField(max_length=32, default="TUITION", db_index=True)
	percentage_bps = models.PositiveIntegerField(
		validators=[MinValueValidator(1), MaxValueValidator(10000)],
	)
	is_active = models.BooleanField(default=True, db_index=True)

	class Meta:
		db_table = "billing_responsibility_rule"
		indexes = [
			models.Index(fields=["school_id", "household", "charge_type", "is_active"], name="billing_res_school__8853ca_idx"),
			models.Index(fields=["school_id", "student", "charge_type", "is_active"], name="billing_res_school__d19f7d_idx"),
		]
		constraints = [
			models.UniqueConstraint(
				fields=["school_id", "household", "payer", "charge_type"],
				condition=models.Q(student__isnull=True),
				name="uniq_household_payer_charge_rule",
			),
			models.UniqueConstraint(
				fields=["school_id", "student", "payer", "charge_type"],
				condition=models.Q(student__isnull=False),
				name="uniq_student_payer_charge_rule",
			),
		]

	def clean(self):
		if self.household_id and self.school_id != self.household.school_id:
			raise ValidationError({"household": "Household must belong to the same school."})
		if self.payer_id:
			if self.school_id != self.payer.school_id or self.household_id != self.payer.household_id:
				raise ValidationError({"payer": "Payer must belong to the same school and household."})
		if self.student_id:
			if self.school_id != self.student.school_id or self.household_id != self.student.household_id:
				raise ValidationError({"student": "Student must belong to the same school and household."})
		if not (self.charge_type or "").strip():
			raise ValidationError({"charge_type": "charge_type is required."})


class InvoicePayerShare(TimeStampedModel):
	"""A payer-facing sub-obligation. The household invoice remains canonical AR truth."""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)
	invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payer_shares")
	payer = models.ForeignKey(BillingPayer, on_delete=models.PROTECT, related_name="invoice_shares")
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	waived_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

	class Meta:
		db_table = "invoice_payer_share"
		indexes = [
			models.Index(fields=["school_id", "payer"], name="invoice_pay_school__f9bd7c_idx"),
			models.Index(fields=["school_id", "invoice"], name="invoice_pay_school__a6db58_idx"),
		]
		constraints = [
			models.UniqueConstraint(fields=["invoice", "payer"], name="uniq_invoice_payer_share"),
			models.CheckConstraint(condition=models.Q(amount__gte=0), name="payer_share_amount_nonnegative"),
			models.CheckConstraint(condition=models.Q(waived_amount__gte=0), name="payer_share_waived_nonnegative"),
			models.CheckConstraint(condition=models.Q(waived_amount__lte=models.F("amount")), name="payer_share_waived_lte_amount"),
		]

	def clean(self):
		if self.invoice_id:
			if self.school_id != self.invoice.school_id:
				raise ValidationError({"invoice": "Invoice must belong to the same school."})
			if self.payer_id and self.invoice.household_id != self.payer.household_id:
				raise ValidationError({"payer": "Payer must belong to the invoice household."})
		if self.payer_id and self.school_id != self.payer.school_id:
			raise ValidationError({"payer": "Payer must belong to the same school."})


class PayerAllocationAttribution(TimeStampedModel):
	"""Attributes a ledger allocation to one payer share without changing ledger ownership."""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	school_id = models.UUIDField(db_index=True)
	share = models.ForeignKey(InvoicePayerShare, on_delete=models.PROTECT, related_name="allocation_attributions")
	allocation = models.ForeignKey("ledger.Allocation", on_delete=models.PROTECT, related_name="payer_attributions")
	amount = models.DecimalField(max_digits=10, decimal_places=2)

	class Meta:
		db_table = "payer_allocation_attribution"
		indexes = [
			models.Index(fields=["school_id", "share"], name="payer_alloc_school__53e532_idx"),
			models.Index(fields=["school_id", "allocation"], name="payer_alloc_school__6c6b39_idx"),
		]
		constraints = [
			models.UniqueConstraint(fields=["share", "allocation"], name="uniq_payer_share_allocation"),
			models.CheckConstraint(condition=models.Q(amount__gt=0), name="payer_attribution_amount_positive"),
		]

	def clean(self):
		if self.share_id and self.school_id != self.share.school_id:
			raise ValidationError({"share": "Payer share must belong to the same school."})
		if self.allocation_id:
			if self.school_id != self.allocation.school_id:
				raise ValidationError({"allocation": "Allocation must belong to the same school."})
			if self.share_id:
				if self.share.invoice.ledger_charge_id != self.allocation.charge_id:
					raise ValidationError({"allocation": "Allocation must apply to the payer share invoice charge."})
