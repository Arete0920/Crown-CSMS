from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from decimal import Decimal


class GLAccount(models.Model):
    """
    Chart of Accounts - General Ledger account definitions.
    Tenant-scoped, hierarchical structure.
    """
    ACCOUNT_TYPES = [
        ("ASSET", "Asset"),
        ("LIABILITY", "Liability"),
        ("EQUITY", "Equity"),
        ("REVENUE", "Revenue"),
        ("EXPENSE", "Expense"),
    ]

    school = models.ForeignKey(
        "core.School",
        on_delete=models.CASCADE,
        related_name="gl_accounts",
    )

    code = models.CharField(max_length=32)
    name = models.CharField(max_length=128)
    account_type = models.CharField(max_length=16, choices=ACCOUNT_TYPES)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="children",
    )
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "journal_gl_account"
        unique_together = ("school", "code")
        indexes = [models.Index(fields=["school", "code"])]

    def __str__(self):
        return f"{self.code} - {self.name}"


class AccountingPeriod(models.Model):
    """
    Tenant-scoped posting period control.

    Periods may be left undefined for backward-compatible operation. Once a
    period exists for a posting date, CLOSED is authoritative and journal
    posting for that date fails closed until the period is explicitly reopened.
    """

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        CLOSED = "CLOSED", "Closed"

    school = models.ForeignKey(
        "core.School",
        on_delete=models.PROTECT,
        related_name="accounting_periods",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="accounting_periods_closed",
    )
    reopened_at = models.DateTimeField(null=True, blank=True)
    reopened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="accounting_periods_reopened",
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "journal_accounting_period"
        ordering = ["school_id", "start_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "start_date", "end_date"],
                name="journal_unique_accounting_period_range",
            ),
            models.CheckConstraint(
                condition=models.Q(end_date__gte=models.F("start_date")),
                name="journal_accounting_period_valid_range",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "start_date", "end_date"]),
            models.Index(fields=["school", "status"]),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError("Accounting period end_date cannot precede start_date.")
        if self.school_id and self.start_date and self.end_date:
            overlap = AccountingPeriod.objects.filter(
                school_id=self.school_id,
                start_date__lte=self.end_date,
                end_date__gte=self.start_date,
            )
            if self.pk:
                overlap = overlap.exclude(pk=self.pk)
            if overlap.exists():
                raise ValidationError("Accounting periods for a school cannot overlap.")

    def contains(self, posting_date):
        return self.start_date <= posting_date <= self.end_date

    def close(self, *, user, note=""):
        if self.status == self.Status.CLOSED:
            return self
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.closed_by = user
        if note:
            self.note = note
        self.full_clean()
        self.save(update_fields=["status", "closed_at", "closed_by", "note", "updated_at"])
        return self

    def reopen(self, *, user, reason):
        reason = (reason or "").strip()
        if not reason:
            raise ValidationError("Reopening an accounting period requires a reason.")
        if self.status == self.Status.OPEN:
            return self
        self.status = self.Status.OPEN
        self.reopened_at = timezone.now()
        self.reopened_by = user
        self.note = f"{self.note}\nREOPEN: {reason}".strip()
        self.full_clean()
        self.save(update_fields=["status", "reopened_at", "reopened_by", "note", "updated_at"])
        return self

    def __str__(self):
        return f"{self.school_id}: {self.start_date} to {self.end_date} ({self.status})"


class JournalEntry(models.Model):
    """
    Immutable journal entry - header for double-entry transactions.
    Once locked (default), cannot be modified or deleted.
    """
    school = models.ForeignKey(
        "core.School",
        on_delete=models.PROTECT,
        related_name="journal_entries",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    posting_date = models.DateField(null=True, blank=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="journal_entries",
    )

    memo = models.TextField(blank=True)
    locked = models.BooleanField(default=True)

    reference_type = models.CharField(max_length=64, blank=True, null=True)
    reference_id = models.UUIDField(blank=True, null=True)

    # Option A accounting contract metadata. These fields preserve the
    # operational journal engine while adopting the stronger cross-domain
    # traceability contract previously modeled in apps.accounting.
    correlation_id = models.UUIDField(blank=True, null=True, db_index=True)
    source_system = models.CharField(max_length=100, default="journal")
    currency = models.CharField(max_length=8, default="USD")

    reversal_of = models.OneToOneField(
        "self",
        null=True,
        blank=True,
        related_name="reversal_entry",
        on_delete=models.PROTECT,
    )

    class Meta:
        db_table = "journal_entry"
        indexes = [
            models.Index(fields=["school", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
        ]

    def clean(self):
        if self.pk and self.locked:
            raise ValidationError("Locked journal entries cannot be modified.")

    def save(self, *args, **kwargs):
        if self.pk:
            original = JournalEntry.objects.get(pk=self.pk)
            if original.locked:
                raise ValidationError("Locked journal entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Journal entries cannot be deleted.")

    def __str__(self):
        return f"Entry {self.id} - {self.memo}"


class JournalLine(models.Model):
    """
    Individual debit/credit line in a journal entry.
    Enforces debit XOR credit (not both, not neither).
    Cannot be modified after entry is locked.
    """
    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.PROTECT,
        related_name="lines",
    )

    account = models.ForeignKey(
        GLAccount,
        on_delete=models.PROTECT,
        related_name="journal_lines",
    )

    debit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    credit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    class Meta:
        db_table = "journal_line"
        indexes = [
            models.Index(fields=["entry", "account"]),
        ]

    def clean(self):
        if self.debit < 0 or self.credit < 0:
            raise ValidationError("Debit and credit must be non-negative.")

        if self.debit > 0 and self.credit > 0:
            raise ValidationError("Line cannot have both debit and credit.")

        if self.debit == 0 and self.credit == 0:
            raise ValidationError("Line must have either debit or credit.")

        if self.account.school_id != self.entry.school_id:
            raise ValidationError("Account school must match entry school.")

    def save(self, *args, **kwargs):
        if self.entry.locked:
            raise ValidationError("Cannot modify lines of a locked entry.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Journal lines cannot be deleted.")

    def __str__(self):
        if self.debit > 0:
            return f"DR {self.account.code}: {self.debit}"
        return f"CR {self.account.code}: {self.credit}"
