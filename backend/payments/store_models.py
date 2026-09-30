"""School store catalog and auditable stock; payment facts remain in Payments."""
from django.conf import settings
from django.db import models

from .models import ImmutableFinancialFact


class StoreProduct(models.Model):
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=160)
    barcode = models.CharField(max_length=64, blank=True, default="")
    price_cents = models.PositiveIntegerField()
    tax_rate_bp = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["school", "sku"], name="store_school_sku_unique"),
            models.UniqueConstraint(fields=["school", "barcode"], condition=~models.Q(barcode=""), name="store_school_barcode_unique"),
            models.CheckConstraint(condition=models.Q(tax_rate_bp__lte=10000), name="store_tax_rate_valid"),
        ]


class StoreStockMovement(ImmutableFinancialFact):
    product = models.ForeignKey(StoreProduct, on_delete=models.PROTECT, related_name="stock_movements")
    delta = models.IntegerField()
    resulting_stock = models.PositiveIntegerField()
    reason = models.CharField(max_length=255)
    idempotency_key = models.CharField(max_length=128)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    immutable_fields = ("product_id", "delta", "resulting_stock", "reason", "idempotency_key", "created_by_id")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "idempotency_key"], name="store_stock_movement_unique"),
            models.CheckConstraint(condition=~models.Q(delta=0), name="store_stock_delta_nonzero"),
        ]
