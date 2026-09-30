"""School-scoped store preparation endpoints, restricted to finance operators."""
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from crown_api.billing_api.permissions import IsFinanceRuntimeUser
from households.scoping import get_request_school_id
from payments.hold import payment_hold_response
from .models import StoreProduct, StoreStockMovement
from .store_services import adjust_stock, quote


class ProductSerializer(serializers.ModelSerializer):
    price_cents = serializers.IntegerField(min_value=0, max_value=2147483647)
    tax_rate_bp = serializers.IntegerField(min_value=0, max_value=10000, default=0)

    class Meta:
        model = StoreProduct
        fields = ["id", "sku", "name", "barcode", "price_cents", "tax_rate_bp", "stock", "active", "updated_at"]
        read_only_fields = ["id", "stock", "updated_at"]
        validators = []  # Tenant-qualified uniqueness is enforced by database constraints.

    def to_internal_value(self, data):
        if not isinstance(data, dict) or set(data) - {"sku", "name", "barcode", "price_cents", "tax_rate_bp", "active"}:
            raise ValidationError({"non_field_errors": ["Unsupported product fields; adjust stock through its audited endpoint."]})
        for field in ("price_cents", "tax_rate_bp"):
            if field in data and type(data[field]) is not int:
                raise ValidationError({field: "Must be an integer."})
        return super().to_internal_value(data)


def save_product(serializer, school_id):
    try:
        with transaction.atomic():
            return serializer.save(school_id=school_id)
    except IntegrityError as exc:
        raise ValidationError("SKU or barcode already exists in this school.") from exc


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsFinanceRuntimeUser])
def products(request):
    school_id = get_request_school_id(request, required=True)
    if request.method == "GET":
        # Bounded catalog pages; retired products remain available for management.
        try:
            page = int(request.query_params.get("page", "1"))
        except ValueError as exc:
            raise ValidationError("Invalid page.") from exc
        if page < 1:
            raise ValidationError("Invalid page.")
        rows = StoreProduct.objects.filter(school_id=school_id)
        count = rows.count()
        return Response({"count": count, "page": page, "results": ProductSerializer(rows[(page-1)*100:page*100], many=True).data})
    serializer = ProductSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    save_product(serializer, school_id)
    return Response(serializer.data, status=201)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated, IsFinanceRuntimeUser])
@transaction.atomic
def product_update(request, product_id):
    school_id = get_request_school_id(request, required=True)
    product = StoreProduct.objects.select_for_update().filter(school_id=school_id, pk=product_id).first()
    if product is None:
        return Response({"detail": "Not found"}, status=404)
    serializer = ProductSerializer(product, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    save_product(serializer, school_id)
    return Response(serializer.data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsFinanceRuntimeUser])
def stock(request, product_id):
    school_id = get_request_school_id(request, required=True)
    if not StoreProduct.objects.filter(pk=product_id, school_id=school_id).exists():
        return Response({"detail": "Not found"}, status=404)
    if request.method == "GET":
        rows = StoreStockMovement.objects.filter(product_id=product_id).order_by("-id")[:100]
        return Response({"results": list(rows.values("id", "delta", "resulting_stock", "reason", "created_by_id", "created_at"))})
    if not isinstance(request.data, dict) or set(request.data) != {"delta", "reason", "idempotency_key"}:
        raise ValidationError("Provide delta, reason, and idempotency_key.")
    movement = adjust_stock(school_id=school_id, product_id=product_id, delta=request.data["delta"],
                            reason=request.data["reason"], key=request.data["idempotency_key"], user=request.user)
    return Response({"movement_id": movement.pk, "resulting_stock": movement.resulting_stock})


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFinanceRuntimeUser])
def cart_quote(request):
    school_id = get_request_school_id(request, required=True)
    if not isinstance(request.data, dict) or set(request.data) != {"items"}:
        raise ValidationError("Provide only items.")
    return Response(quote(school_id=school_id, items=request.data["items"]))


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsFinanceRuntimeUser])
def checkout(request):
    get_request_school_id(request, required=True)
    # No payload validation or mutations while canonical payment hold is active.
    return payment_hold_response()
