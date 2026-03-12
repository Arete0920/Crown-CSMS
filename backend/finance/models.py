from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone
from core.models import School, AcademicYear, UserAccount


# ---------------------------------------------------------------------------
# Enumerations used by Phase 8 Finance models
# ---------------------------------------------------------------------------

class MoneyStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    OPEN = "open", "Open"
    PAID = "paid", "Paid"
    VOID = "void", "Void"
    REFUNDED = "refunded", "Refunded"


class ObligationType(models.TextChoices):
    TUITION = "tuition", "Tuition"
    FEE = "fee", "Fee"
    INCIDENTAL = "incidental", "Incidental"
    DONATION_PLEDGE = "donation_pledge", "Donation Pledge"


class PaymentStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SETTLED = "settled", "Settled"
    FAILED = "failed", "Failed"
    VOID = "void", "Void"
    REFUNDED = "refunded", "Refunded"


class Processor(models.TextChoices):
    MANUAL = "manual", "Manual"
    STRIPE = "stripe", "Stripe"
    COMPUWERX = "compuwerx", "Compuwerx"


class ChartAccount(models.Model):
    """
    Lightweight Chart of Accounts using CODE (e.g., TUITION, AID, FEES, PAYMENT, AR).
    Each code has an account_type for basic financial categorization.
    """
    ACCOUNT_TYPE_CHOICES = [
        ('ASSET', 'Asset'),
        ('LIABILITY', 'Liability'),
        ('INCOME', 'Income'),
        ('EXPENSE', 'Expense'),
        ('EQUITY', 'Equity'),
    ]

    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name='chart_accounts')
    code = models.CharField(max_length=32)  # e.g., TUITION, AID, FEES, PAYMENT, AR
    name = models.CharField(max_length=120)  # e.g., "Tuition Revenue", "Financial Aid"
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default='INCOME')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('school', 'code')]
        indexes = [
            models.Index(fields=['school', 'code']),
        ]

    def __str__(self):
        return f"{self.code} — {self.name} ({self.account_type})"


class JournalBatch(models.Model):
    """
    Groups a set of LedgerEntry postings together for audit/rollback.
    Example: 'Annual tuition posting for 2025–26' or 'Q1 aid awards'.
    """
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('POSTED', 'Posted'),
        ('VOID', 'Void'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='journal_batches')
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name='journal_batches', null=True, blank=True)
    batch_date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')
    created_by = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-batch_date']

    def __str__(self):
        return f"Batch {self.id} – {self.description} ({self.status})"


# ---------------------------------------------------------------------------
# Phase 8: Finance & Tuition domain models
# ---------------------------------------------------------------------------

class FinanceObligation(models.Model):
    """What a family owes (tuition plan, fee assessment, etc.)."""
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="finance_obligations")
    payer_user = models.ForeignKey(
        UserAccount, on_delete=models.PROTECT, related_name="finance_obligations"
    )
    obligation_type = models.CharField(max_length=32, choices=ObligationType.choices, default=ObligationType.TUITION)
    status = models.CharField(max_length=16, choices=MoneyStatus.choices, default=MoneyStatus.OPEN)

    description = models.CharField(max_length=255)
    due_date = models.DateField(db_index=True)
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=8, default="USD")

    academic_year_label = models.CharField(max_length=9, blank=True, default="")  # e.g. "2025-2026"
    reference = models.CharField(max_length=64, blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        UserAccount, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_finance_obligations"
    )
    updated_by = models.ForeignKey(
        UserAccount, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="updated_finance_obligations"
    )

    class Meta:
        indexes = [
            models.Index(fields=["school", "payer_user", "status"]),
            models.Index(fields=["school", "due_date"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gte=0),
                name="finance_obligation_amount_cents_nonneg"
            ),
        ]

    def __str__(self) -> str:
        return (
            f"Obligation {self.id} | {self.school_id} | {self.obligation_type} | "
            f"{self.amount_cents}¢ | {self.status}"
        )


class FinanceInvoice(models.Model):
    """Presentation layer grouping obligations for a period."""
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="finance_invoices")
    payer_user = models.ForeignKey(
        UserAccount, on_delete=models.PROTECT, related_name="finance_invoices"
    )
    status = models.CharField(max_length=16, choices=MoneyStatus.choices, default=MoneyStatus.OPEN)

    period_start = models.DateField()
    period_end = models.DateField()
    issued_at = models.DateTimeField(default=timezone.now)
    due_date = models.DateField(db_index=True)

    # Snapshot totals — source of truth is obligations + allocations
    subtotal_cents = models.PositiveIntegerField(default=0)
    total_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default="USD")
    note = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        UserAccount, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_finance_invoices"
    )

    class Meta:
        indexes = [
            models.Index(fields=["school", "payer_user", "status"]),
            models.Index(fields=["school", "due_date"]),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.id} | {self.school_id} | {self.total_cents}¢ | {self.status}"


class FinanceInvoiceLine(models.Model):
    """Single line item on an invoice, linked to an obligation."""
    invoice = models.ForeignKey(FinanceInvoice, on_delete=models.CASCADE, related_name="lines")
    obligation = models.ForeignKey(
        FinanceObligation, on_delete=models.PROTECT, related_name="invoice_lines"
    )
    amount_cents = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = [("invoice", "obligation")]


class FinancePayment(models.Model):
    """Money received from a payer (before or after processor settlement)."""
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="finance_payments")
    payer_user = models.ForeignKey(
        UserAccount, on_delete=models.PROTECT, related_name="finance_payments"
    )
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=8, default="USD")

    processor = models.CharField(max_length=16, choices=Processor.choices, default=Processor.MANUAL)
    processor_payment_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, default="", db_index=True)

    received_at = models.DateTimeField(null=True, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        UserAccount, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_finance_payments"
    )

    class Meta:
        indexes = [
            models.Index(fields=["school", "payer_user", "status"]),
            models.Index(fields=["school", "processor", "processor_payment_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gte=0),
                name="finance_payment_amount_cents_nonneg"
            ),
        ]

    def __str__(self) -> str:
        return f"Payment {self.id} | {self.amount_cents}¢ | {self.status}"


class FinanceAllocation(models.Model):
    """Applies a payment (or portion) to an obligation."""
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="finance_allocations")
    payment = models.ForeignKey(FinancePayment, on_delete=models.CASCADE, related_name="allocations")
    obligation = models.ForeignKey(
        FinanceObligation, on_delete=models.PROTECT, related_name="allocations"
    )
    amount_cents = models.PositiveIntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["school", "obligation"]),
            models.Index(fields=["school", "payment"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gt=0),
                name="finance_allocation_amount_positive"
            ),
        ]


class FinanceRefund(models.Model):
    """Reversal of a prior payment, posted as a ledger reversal pair."""
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="finance_refunds")
    payment = models.ForeignKey(FinancePayment, on_delete=models.PROTECT, related_name="refunds")
    status = models.CharField(max_length=16, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)

    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=8, default="USD")

    processor = models.CharField(max_length=16, choices=Processor.choices, default=Processor.MANUAL)
    processor_refund_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(max_length=128, blank=True, default="", db_index=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        UserAccount, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="created_finance_refunds"
    )

    class Meta:
        indexes = [
            models.Index(fields=["school", "processor", "processor_refund_id"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount_cents__gt=0),
                name="finance_refund_amount_positive"
            ),
        ]


class FinanceDonation(models.Model):
    """Giving/donation separate from tuition (still ledger-integrated)."""
    school = models.ForeignKey(School, on_delete=models.PROTECT, related_name="finance_donations")
    donor_user = models.ForeignKey(
        UserAccount, on_delete=models.PROTECT, related_name="finance_donations"
    )
    status = models.CharField(max_length=16, choices=MoneyStatus.choices, default=MoneyStatus.OPEN)

    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=8, default="USD")

    fund_code = models.CharField(max_length=64, blank=True, default="")
    memo = models.CharField(max_length=255, blank=True, default="")

    is_recurring = models.BooleanField(default=False)
    recurring_rule = models.CharField(max_length=128, blank=True, default="")
    next_run_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "donor_user", "status"]),
            models.Index(fields=["school", "fund_code"]),
        ]

    def __str__(self) -> str:
        return f"Donation {self.id} | {self.school_id} | {self.fund_code} | {self.amount_cents}¢"
