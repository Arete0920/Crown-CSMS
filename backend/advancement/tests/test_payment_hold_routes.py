"""Regression tests for Advancement payment holds and privileged route authority."""

import uuid
from types import SimpleNamespace
from unittest.mock import patch

from django.test import RequestFactory, SimpleTestCase
from django.urls import resolve, reverse
from rest_framework.test import APIRequestFactory, force_authenticate

from advancement.payment_hold_views import (
    advancement_edit_post_payment_on_hold,
    advancement_view_get_payment_on_hold,
    advancement_view_post_payment_on_hold,
    authenticated_post_payment_on_hold,
    provider_webhook_not_configured,
)
from payments.exceptions_api import payment_exception_retry
from payments.hold import PAYMENT_INTEGRATION_ON_HOLD, payment_hold_response


class ExternalPaymentHoldRouteTest(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.sample_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    def assert_methods(self, view, *, allowed):
        configured = set(view.cls.http_method_names)
        self.assertTrue(set(allowed).issubset(configured))
        for method in {"get", "post"} - set(allowed):
            self.assertNotIn(method, configured)

    def test_authenticated_provider_routes_use_post_only_hold(self):
        held_routes = [
            ("advancement-purchase-ticket", {}),
            ("advancement-purchase-store", {}),
            ("advancement-gift-checkout", {}),
            ("advancement-sponsorship-checkout", {}),
        ]

        for route_name, kwargs in held_routes:
            with self.subTest(route_name=route_name):
                match = resolve(reverse(route_name, kwargs=kwargs))
                self.assertIs(match.func, authenticated_post_payment_on_hold)
                self.assert_methods(match.func, allowed={"post"})

    def test_privileged_payment_marking_routes_require_advancement_edit(self):
        edit_routes = [
            ("advancement-gift-mark-paid", {"gift_id": self.sample_id}),
            ("advancement-sponsorship-mark-paid", {"agreement_id": self.sample_id}),
            ("advancement-seating-purchase-held", {}),
        ]
        for route_name, kwargs in edit_routes:
            with self.subTest(route_name=route_name):
                match = resolve(reverse(route_name, kwargs=kwargs))
                self.assertIs(match.func, advancement_edit_post_payment_on_hold)
                self.assert_methods(match.func, allowed={"post"})

    def test_advancement_view_permission_routes_keep_original_methods(self):
        post_routes = [
            ("advancement-seating-checkout", {}),
            ("advancement-best-available-checkout", {}),
        ]
        for route_name, kwargs in post_routes:
            with self.subTest(route_name=route_name):
                match = resolve(reverse(route_name, kwargs=kwargs))
                self.assertIs(match.func, advancement_view_post_payment_on_hold)
                self.assert_methods(match.func, allowed={"post"})

        status_match = resolve(
            reverse("advancement-order-status", kwargs={"order_id": self.sample_id})
        )
        self.assertIs(status_match.func, advancement_view_get_payment_on_hold)
        self.assert_methods(status_match.func, allowed={"get"})

    def test_privileged_nonpayment_routes_fail_closed_without_persistent_permission(self):
        routes = [
            ("get", "advancement-summary", {}),
            ("post", "advancement-pledge-cancel", {"pledge_id": self.sample_id}),
            ("post", "advancement-qr-checkin", {}),
        ]
        user = SimpleNamespace(is_authenticated=True)
        school = SimpleNamespace(id=self.sample_id)

        with patch("core.permissions.user_has_permission", return_value=False):
            for method, route_name, kwargs in routes:
                with self.subTest(route_name=route_name):
                    route = reverse(route_name, kwargs=kwargs)
                    request = getattr(self.factory, method)(route, data={})
                    request.user = user
                    request.school = school
                    response = resolve(route).func(request, **kwargs)
                    self.assertEqual(response.status_code, 403)

    def test_provider_webhook_is_not_exposed(self):
        route = reverse("advancement-stripe-webhook")
        match = resolve(route)
        self.assertIs(match.func, provider_webhook_not_configured)
        response = match.func(
            self.factory.post(route, data=b"{}", content_type="application/json")
        )
        self.assertEqual(response.status_code, 404)

    def test_provider_neutral_reservation_and_read_routes_remain_available(self):
        allowed_routes = [
            ("advancement-pledge-create", {}),
            ("advancement-seating-availability", {}),
            ("advancement-seating-hold-strict", {}),
            ("advancement-section-prices", {"event_id": self.sample_id}),
        ]

        held_functions = {
            authenticated_post_payment_on_hold,
            advancement_edit_post_payment_on_hold,
            advancement_view_post_payment_on_hold,
            advancement_view_get_payment_on_hold,
            provider_webhook_not_configured,
        }
        for route_name, kwargs in allowed_routes:
            with self.subTest(route_name=route_name):
                match = resolve(reverse(route_name, kwargs=kwargs))
                self.assertNotIn(match.func, held_functions)

    def test_canonical_hold_payload_is_structured_and_provider_neutral(self):
        response = payment_hold_response()
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, PAYMENT_INTEGRATION_ON_HOLD)
        self.assertEqual(response.data["code"], "payment_integration_on_hold")
        self.assertIs(response.data["provider_configured"], False)
        self.assertIsNone(response.data["provider"])

    def test_held_route_still_denies_unauthenticated_requests(self):
        route = reverse("advancement-gift-checkout")
        response = resolve(route).func(self.factory.post(route, data={}))
        self.assertIn(response.status_code, {401, 403})


class GatewayRetryHoldTest(SimpleTestCase):
    def test_retry_returns_before_exception_or_gateway_event_access(self):
        request = APIRequestFactory().post("/api/v1/payments/exceptions/7/retry/", {})
        force_authenticate(
            request,
            user=SimpleNamespace(is_authenticated=True, is_active=True),
        )

        with (
            patch("payments.exceptions_api.get_request_school_id", return_value=self.sample_school_id()),
            patch("payments.exceptions_api._finance_only", return_value=True),
            patch("payments.exceptions_api.PaymentSupportException.objects.filter") as filter_mock,
        ):
            response = payment_exception_retry(request, exception_id=7)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, PAYMENT_INTEGRATION_ON_HOLD)
        filter_mock.assert_not_called()

    @staticmethod
    def sample_school_id():
        return uuid.UUID("00000000-0000-0000-0000-000000000002")
