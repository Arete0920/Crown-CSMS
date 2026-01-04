from django.db import models
from django.utils import timezone
from core.models import School, AcademicYear, UserAccount


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
