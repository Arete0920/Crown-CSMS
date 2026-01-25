from django.db import models

from core.models import BaseModel
from crown_api.models_households import Household


class Invoice(BaseModel):
    STATUS_OPEN = "OPEN"
    STATUS_PAID = "PAID"
    STATUS_VOID = "VOID"

    STATUS_CHOICES = [
        (STATUS_OPEN, "Open"),
        (STATUS_PAID, "Paid"),
        (STATUS_VOID, "Void"),
    ]

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    invoice_number = models.CharField(max_length=32, unique=True, db_index=True)
    amount_cents = models.IntegerField()
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=STATUS_OPEN)
    due_date = models.DateField(null=True, blank=True)
    issued_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-issued_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.invoice_number} ({self.household})"


class Payment(BaseModel):
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    payment_reference = models.CharField(max_length=48, unique=True, db_index=True)
    amount_cents = models.IntegerField()
    payment_date = models.DateField(db_index=True)

    class Meta:
        ordering = ["-payment_date", "-created_at"]

    def __str__(self) -> str:
        return f"{self.payment_reference} ({self.household})"
