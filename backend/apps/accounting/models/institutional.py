import uuid
from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils import timezone


def _uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (TypeError, ValueError, AttributeError):
        return value


def _require_tenant(instance, relation_name: str, *, relation_tenant_attr: str = "tenant_id") -> None:
    relation_id = getattr(instance, f"{relation_name}_id", None)
    if relation_id is None:
        return
    try:
        related = getattr(instance, relation_name)
    except ObjectDoesNotExist as exc:
        raise ValidationError({relation_name: "Related record does not exist."}) from exc
    if _uuid(instance.tenant_id) != _uuid(getattr(related, relation_tenant_attr)):
        raise ValidationError({relation_name: "Related record must belong to the same tenant."})


class TenantAccountingModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        raise ValidationError("Accounting business records cannot be hard deleted.")


class Fund(TenantAccountingModel):
    class Restriction(models.TextChoices):
        UNRESTRICTED = "UNRESTRICTED", "Unrestricted"
        RESTRICTED = "RESTRICTED", "Restricted"
        BOARD_DESIGNATED = "BOARD_DESIGNATED", "Board designated"

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    restriction = models.CharField(max_length=24, choices=Restriction.choices, default=Restriction.UNRESTRICTED)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounting_fund"
        constraints = [models.UniqueConstraint(fields=["tenant_id", "code"], name="accounting_fund_tenant_code_uq")]
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountingDimension(TenantAccountingModel):
    class Kind(models.TextChoices):
        DEPARTMENT = "DEPARTMENT", "Department"
        PROGRAM = "PROGRAM", "Program"
        CAMPUS = "CAMPUS", "Campus"
        PROJECT = "PROJECT", "Project"

    kind = models.CharField(max_length=16, choices=Kind.choices)
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounting_dimension"
        constraints = [models.UniqueConstraint(fields=["tenant_id", "kind", "code"], name="accounting_dimension_tenant_kind_code_uq")]
        ordering = ["kind", "code"]

    def __str__(self):
        return f"{self.kind}:{self.code} - {self.name}"


class Vendor(TenantAccountingModel):
    code = models.CharField(max_length=32)
    legal_name = models.CharField(max_length=200)
    display_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    payment_terms_days = models.PositiveSmallIntegerField(default=30)
    default_expense_account = models.ForeignKey(
        "journal.GLAccount", null=True, blank=True, on_delete=models.PROTECT, related_name="default_vendors"
    )
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounting_vendor"
        constraints = [models.UniqueConstraint(fields=["tenant_id", "code"], name="accounting_vendor_tenant_code_uq")]
        ordering = ["display_name", "legal_name"]

    def clean(self):
        super().clean()
        _require_tenant(self, "default_expense_account", relation_tenant_attr="school_id")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name or self.legal_name


class PurchaseOrder(TenantAccountingModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        CLOSED = "CLOSED", "Closed"
        CANCELLED = "CANCELLED", "Cancelled"

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="purchase_orders")
    number = models.CharField(max_length=48)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    ordered_on = models.DateField(default=timezone.localdate)
    expected_on = models.DateField(null=True, blank=True)
    currency = models.CharField(max_length=8, default="USD")
    memo = models.TextField(blank=True)
    created_by = models.UUIDField()
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounting_purchase_order"
        constraints = [models.UniqueConstraint(fields=["tenant_id", "number"], name="accounting_po_tenant_number_uq")]
        ordering = ["-ordered_on", "number"]

    def clean(self):
        super().clean()
        _require_tenant(self, "vendor")
        if self.expected_on and self.expected_on < self.ordered_on:
            raise ValidationError({"expected_on": "Expected date cannot precede order date."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return sum((line.line_total for line in self.lines.all()), Decimal("0.00"))


class PurchaseOrderLine(TenantAccountingModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="lines")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("1.00"))
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)
    account = models.ForeignKey("journal.GLAccount", on_delete=models.PROTECT, related_name="purchase_order_lines")
    fund = models.ForeignKey(Fund, null=True, blank=True, on_delete=models.PROTECT, related_name="purchase_order_lines")
    dimension = models.ForeignKey(AccountingDimension, null=True, blank=True, on_delete=models.PROTECT, related_name="purchase_order_lines")

    class Meta:
        db_table = "accounting_purchase_order_line"
        ordering = ["created_at"]

    def clean(self):
        super().clean()
        _require_tenant(self, "purchase_order")
        _require_tenant(self, "account", relation_tenant_attr="school_id")
        _require_tenant(self, "fund")
        _require_tenant(self, "dimension")
        if self.quantity <= 0:
            raise ValidationError({"quantity": "Quantity must be positive."})
        if self.unit_cost < 0:
            raise ValidationError({"unit_cost": "Unit cost cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def line_total(self):
        return (self.quantity * self.unit_cost).quantize(Decimal("0.01"))


class PayableBill(TenantAccountingModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        POSTED = "POSTED", "Posted"
        PAID = "PAID", "Paid"
        VOID = "VOID", "Void"

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT, related_name="bills")
    purchase_order = models.ForeignKey(PurchaseOrder, null=True, blank=True, on_delete=models.PROTECT, related_name="bills")
    bill_number = models.CharField(max_length=64)
    bill_date = models.DateField()
    due_date = models.DateField()
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=8, default="USD")
    liability_account = models.ForeignKey("journal.GLAccount", on_delete=models.PROTECT, related_name="payable_bills")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    memo = models.TextField(blank=True)
    created_by = models.UUIDField()
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    journal_entry = models.ForeignKey("journal.JournalEntry", null=True, blank=True, on_delete=models.PROTECT, related_name="payable_bills")

    class Meta:
        db_table = "accounting_payable_bill"
        constraints = [models.UniqueConstraint(fields=["tenant_id", "vendor", "bill_number"], name="accounting_bill_tenant_vendor_number_uq")]
        ordering = ["due_date", "bill_date"]

    def clean(self):
        super().clean()
        _require_tenant(self, "vendor")
        _require_tenant(self, "purchase_order")
        _require_tenant(self, "liability_account", relation_tenant_attr="school_id")
        _require_tenant(self, "journal_entry", relation_tenant_attr="school_id")
        if self.purchase_order_id and self.purchase_order.vendor_id != self.vendor_id:
            raise ValidationError({"purchase_order": "Purchase order vendor must match bill vendor."})
        if self.due_date < self.bill_date:
            raise ValidationError({"due_date": "Due date cannot precede bill date."})
        if self.total_amount <= 0:
            raise ValidationError({"total_amount": "Bill total must be positive."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class PayableBillLine(TenantAccountingModel):
    bill = models.ForeignKey(PayableBill, on_delete=models.PROTECT, related_name="lines")
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    expense_account = models.ForeignKey("journal.GLAccount", on_delete=models.PROTECT, related_name="payable_bill_lines")
    fund = models.ForeignKey(Fund, null=True, blank=True, on_delete=models.PROTECT, related_name="payable_bill_lines")
    dimension = models.ForeignKey(AccountingDimension, null=True, blank=True, on_delete=models.PROTECT, related_name="payable_bill_lines")

    class Meta:
        db_table = "accounting_payable_bill_line"
        ordering = ["created_at"]

    def clean(self):
        super().clean()
        _require_tenant(self, "bill")
        _require_tenant(self, "expense_account", relation_tenant_attr="school_id")
        _require_tenant(self, "fund")
        _require_tenant(self, "dimension")
        if self.amount <= 0:
            raise ValidationError({"amount": "Bill line amount must be positive."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class Budget(TenantAccountingModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        CLOSED = "CLOSED", "Closed"

    name = models.CharField(max_length=128)
    fiscal_start = models.DateField()
    fiscal_end = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    approved_by = models.UUIDField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "accounting_budget"
        constraints = [models.UniqueConstraint(fields=["tenant_id", "name", "fiscal_start", "fiscal_end"], name="accounting_budget_period_name_uq")]
        ordering = ["-fiscal_start", "name"]

    def clean(self):
        super().clean()
        if self.fiscal_end < self.fiscal_start:
            raise ValidationError({"fiscal_end": "Fiscal end cannot precede fiscal start."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def total_amount(self):
        return sum((line.amount for line in self.lines.all()), Decimal("0.00"))


class BudgetLine(TenantAccountingModel):
    budget = models.ForeignKey(Budget, on_delete=models.PROTECT, related_name="lines")
    account = models.ForeignKey("journal.GLAccount", on_delete=models.PROTECT, related_name="budget_lines")
    fund = models.ForeignKey(Fund, null=True, blank=True, on_delete=models.PROTECT, related_name="budget_lines")
    dimension = models.ForeignKey(AccountingDimension, null=True, blank=True, on_delete=models.PROTECT, related_name="budget_lines")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "accounting_budget_line"
        ordering = ["account__code", "created_at"]

    def clean(self):
        super().clean()
        _require_tenant(self, "budget")
        _require_tenant(self, "account", relation_tenant_attr="school_id")
        _require_tenant(self, "fund")
        _require_tenant(self, "dimension")
        if self.amount < 0:
            raise ValidationError({"amount": "Budget amount cannot be negative."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
