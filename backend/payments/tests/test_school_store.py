from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory, force_authenticate

from core.models import School
from payments import store_api
from payments.hold import PAYMENT_INTEGRATION_ON_HOLD
from payments.models import Payment, StoreProduct, StoreStockMovement
from payments.store_services import adjust_stock, quote


class SchoolStoreTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Store School")
        self.other = School.objects.create(name="Other School")
        self.user = get_user_model().objects.create_user(username="store-manager", school=self.school, is_superuser=True)
        self.product = StoreProduct.objects.create(school=self.school, sku="SHIRT-M", name="School shirt medium", price_cents=1999, tax_rate_bp=600)
        self.factory = APIRequestFactory()

    def adjust(self, delta=5, key="delivery-1"):
        return adjust_stock(school_id=self.school.pk, product_id=self.product.pk, delta=delta, reason="Delivery", key=key, user=self.user)

    def request(self, method, path, payload=None, user=None):
        request = getattr(self.factory, method)(path, payload or {}, format="json", HTTP_X_SCHOOL_ID=str(self.school.pk))
        force_authenticate(request, user=user or self.user)
        return request

    def test_stock_is_audited_idempotent_and_conflicts_fail(self):
        first = self.adjust()
        self.assertEqual(first.pk, self.adjust().pk)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertEqual(StoreStockMovement.objects.count(), 1)
        with self.assertRaises(ValidationError):
            self.adjust(6)
        with self.assertRaises(ValidationError):
            self.adjust(-6, "negative")
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)

    def test_stock_audit_cannot_be_rewritten_or_deleted(self):
        movement = self.adjust()
        movement.delta = 10
        with self.assertRaises(DjangoValidationError):
            movement.save()
        with self.assertRaises(DjangoValidationError):
            StoreStockMovement.objects.all().delete()

    def test_server_pricing_tax_rounding_and_no_reservation(self):
        self.adjust()
        result = quote(school_id=self.school.pk, items=[{"product_id": self.product.pk, "quantity": 2}])
        self.assertEqual((result["subtotal_cents"], result["tax_cents"], result["total_cents"]), (3998, 240, 4238))
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)
        self.assertFalse(result["stock_reserved"])
        self.assertFalse(result["payment_enabled"])
        self.assertEqual(Payment.objects.count(), 0)

    def test_duplicates_are_aggregated_before_stock_check(self):
        self.adjust()
        with self.assertRaises(ValidationError):
            quote(school_id=self.school.pk, items=[{"product_id": self.product.pk, "quantity": 3}] * 2)

    def test_foreign_inactive_and_invalid_items_fail(self):
        self.adjust()
        for items in ([], [{"product_id": self.product.pk, "quantity": True}],
                      [{"product_id": self.product.pk, "quantity": 1.5}],
                      [{"product_id": self.product.pk, "quantity": 1, "price_cents": 1}]):
            with self.assertRaises(ValidationError):
                quote(school_id=self.school.pk, items=items)
        with self.assertRaises(ValidationError):
            quote(school_id=self.other.pk, items=[{"product_id": self.product.pk, "quantity": 1}])
        with self.assertRaises(StoreProduct.DoesNotExist):
            adjust_stock(school_id=self.other.pk, product_id=self.product.pk, delta=1, reason="Bad", key="bad", user=self.user)
        self.product.active = False
        self.product.save()
        with self.assertRaises(ValidationError):
            quote(school_id=self.school.pk, items=[{"product_id": self.product.pk, "quantity": 1}])

    def test_checkout_hold_has_no_side_effects_even_for_malformed_payload(self):
        response = store_api.checkout(self.request("post", "/api/v1/payments/store/checkout/", {"card_number": "forbidden"}))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, PAYMENT_INTEGRATION_ON_HOLD)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(StoreStockMovement.objects.count(), 0)

    def test_catalog_api_creation_uniqueness_and_stock_field_rejection(self):
        path = "/api/v1/payments/store/products/"
        data = {"sku": "BOOK", "name": "Book", "price_cents": 1000}
        self.assertEqual(store_api.products(self.request("post", path, data)).status_code, 201)
        self.assertEqual(store_api.products(self.request("post", path, data)).status_code, 400)
        self.assertEqual(store_api.products(self.request("post", path, {**data, "stock": 100})).status_code, 400)
        result = store_api.products(self.request("get", path))
        self.assertEqual(result.data["count"], 2)
        foreign = StoreProduct.objects.create(school=self.other, sku="BOOK", name="Other book", price_cents=1000)
        response = store_api.product_update(self.request("patch", path, {"price_cents": 1}), foreign.pk)
        self.assertEqual(response.status_code, 404)

    def test_unauthorized_user_cannot_manage_or_checkout(self):
        user = get_user_model().objects.create_user(username="student", email="student@school.test", school=self.school)
        for view in (store_api.products, store_api.cart_quote, store_api.checkout):
            response = view(self.request("post", "/api/v1/payments/store/", {}, user=user))
            self.assertEqual(response.status_code, 403)

    def test_tenant_header_cannot_override_normal_user_school(self):
        from django.contrib.auth.models import Group
        user = get_user_model().objects.create_user(username="local-finance", email="finance@school.test", school=self.school)
        user.groups.add(Group.objects.create(name="finance_admin"))
        request = self.factory.get("/api/v1/payments/store/products/", HTTP_X_SCHOOL_ID=str(self.other.pk))
        force_authenticate(request, user=user)
        self.assertEqual(store_api.products(request).status_code, 404)
