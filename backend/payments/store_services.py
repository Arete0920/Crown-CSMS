"""Inventory changes and server-priced quotations; no payment collection."""
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import CampusSalesArea, StoreProduct, StoreStockMovement


def integer(value, field, *, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError({field: f"Must be an integer from {minimum} to {maximum}."})
    return value


@transaction.atomic
def adjust_stock(*, school_id, product_id, delta, reason, key, user):
    integer(delta, "delta", minimum=-1000000, maximum=1000000)
    if delta == 0 or not isinstance(reason, str) or not reason.strip() or len(reason) > 255:
        raise ValidationError("A nonzero adjustment and a reason of at most 255 characters are required.")
    if not isinstance(key, str) or not key.strip() or len(key) > 128:
        raise ValidationError("A stock idempotency key of at most 128 characters is required.")
    product = StoreProduct.objects.select_for_update().get(pk=product_id, school_id=school_id)
    previous = StoreStockMovement.objects.filter(product=product, idempotency_key=key).first()
    if previous:
        if (previous.delta, previous.reason, previous.created_by_id) != (delta, reason.strip(), user.pk):
            raise ValidationError("Stock idempotency key conflicts with the original adjustment.")
        return previous
    resulting = product.stock + delta
    if not 0 <= resulting <= 2147483647:
        raise ValidationError("Adjustment would put stock outside the supported range.")
    product.stock = resulting
    product.save(update_fields=["stock", "updated_at"])
    return StoreStockMovement.objects.create(product=product, delta=delta, resulting_stock=resulting,
                                             reason=reason.strip(), idempotency_key=key, created_by=user)


def validate_sales_area(value):
    if not isinstance(value, str) or value not in CampusSalesArea.values:
        raise ValidationError({"sales_area": "Select store, snack, or lunch."})
    return value


def quote(*, school_id, items, sales_area="store"):
    validate_sales_area(sales_area)
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ValidationError("Provide between 1 and 100 cart items.")
    quantities = {}
    for item in items:
        if not isinstance(item, dict) or set(item) != {"product_id", "quantity"}:
            raise ValidationError("Cart items require only product_id and quantity; prices are server-owned.")
        product_id = integer(item["product_id"], "product_id", minimum=1, maximum=9223372036854775807)
        quantity = integer(item["quantity"], "quantity", minimum=1, maximum=1000)
        quantities[product_id] = quantities.get(product_id, 0) + quantity
        if quantities[product_id] > 1000:
            raise ValidationError("Maximum quantity per product is 1000.")
    products = list(StoreProduct.objects.filter(school_id=school_id, sales_area=sales_area, active=True, pk__in=quantities).order_by("pk"))
    if len(products) != len(quantities):
        raise ValidationError("One or more products are unavailable in this school and sales area.")
    lines = []
    for product in products:
        quantity = quantities[product.pk]
        if quantity > product.stock:
            raise ValidationError({"stock": f"Insufficient stock for {product.sku}."})
        subtotal = product.price_cents * quantity
        # USD: round half up per product line, using integer basis points.
        tax = (subtotal * product.tax_rate_bp + 5000) // 10000
        lines.append({"product_id": product.pk, "sku": product.sku, "name": product.name,
                      "quantity": quantity, "unit_price_cents": product.price_cents,
                      "subtotal_cents": subtotal, "tax_cents": tax, "total_cents": subtotal + tax})
    subtotal = sum(line["subtotal_cents"] for line in lines)
    tax = sum(line["tax_cents"] for line in lines)
    return {"currency": "USD", "sales_area": sales_area, "items": lines, "subtotal_cents": subtotal, "tax_cents": tax,
            "total_cents": subtotal + tax, "payment_enabled": False, "stock_reserved": False,
            "status": "quote"}
