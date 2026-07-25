"""Direct proof for provider-dependent payment routes held by product authority."""

import uuid
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from payments.api_views import create_payment_intent, payment_intent_status
from payments.disputes_api import dispute_action_create
from payments.exceptions_api import payment_exception_retry
from payments.hold import PAYMENT_INTEGRATION_ON_HOLD
from payments.methods_api import create_payment_method_setup, detach_payment_method


class ProviderPaymentFailClosedTest(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = SimpleNamespace(is_authenticated=True, is_active=True)
        self.school_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        self.household_id = uuid.UUID("00000000-0000-0000-0000-000000000003")

    def authenticated(self, request):
        force_authenticate(request, user=self.user)
        return request

    def assert_hold(self, response):
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.data, PAYMENT_INTEGRATION_ON_HOLD)
        self.assertEqual(response.data["code"], "payment_integration_on_hold")
        self.assertIs(response.data["provider_configured"], False)
        self.assertIsNone(response.data["provider"])
        self.assertNotIn("intent_id", response.data)
        self.assertNotIn("method_id", response.data)
        self.assertNotIn("dispute_id", response.data)
        self.assertNotIn("exception_id", response.data)

    def test_intent_create_and_status_use_the_canonical_provider_neutral_hold(self):
        create_response = create_payment_intent(
            self.authenticated(self.factory.post("/api/v1/payments/intents/", {}))
        )
        status_response = payment_intent_status(
            self.authenticated(
                self.factory.get("/api/v1/payments/intents/provider-secret/status/")
            ),
            intent_id="provider-secret",
        )

        self.assert_hold(create_response)
        self.assert_hold(status_response)

    def test_saved_method_setup_and_detach_hold_before_provider_record_access(self):
        setup_request = self.authenticated(
            self.factory.post(
                f"/api/v1/payments/accounts/{self.household_id}/methods/setup/", {}
            )
        )
        detach_request = self.authenticated(
            self.factory.delete(
                f"/api/v1/payments/accounts/{self.household_id}/methods/71/"
            )
        )

        with (
            patch(
                "payments.methods_api.get_request_school_id",
                return_value=self.school_id,
            ),
            patch(
                "payments.methods_api.user_can_access_household_finance",
                return_value=True,
            ),
            patch("payments.methods_api.SavedPaymentMethod.objects.filter") as filter_mock,
        ):
            setup_response = create_payment_method_setup(
                setup_request, household_id=self.household_id
            )
            detach_response = detach_payment_method(
                detach_request, household_id=self.household_id, method_id=71
            )

        self.assert_hold(setup_response)
        self.assert_hold(detach_response)
        filter_mock.assert_not_called()

    def test_dispute_action_and_exception_retry_hold_before_provider_record_access(self):
        dispute_request = self.authenticated(
            self.factory.post("/api/v1/payments/disputes/29/actions/", {})
        )
        retry_request = self.authenticated(
            self.factory.post("/api/v1/payments/exceptions/37/retry/", {})
        )

        with (
            patch(
                "payments.disputes_api.get_request_school_id",
                return_value=self.school_id,
            ),
            patch("payments.disputes_api._finance_only", return_value=True),
            patch("payments.disputes_api.ProviderDispute.objects.filter") as dispute_filter,
        ):
            dispute_response = dispute_action_create(dispute_request, dispute_id=29)

        with (
            patch(
                "payments.exceptions_api.get_request_school_id",
                return_value=self.school_id,
            ),
            patch("payments.exceptions_api._finance_only", return_value=True),
            patch(
                "payments.exceptions_api.PaymentSupportException.objects.filter"
            ) as exception_filter,
        ):
            retry_response = payment_exception_retry(retry_request, exception_id=37)

        self.assert_hold(dispute_response)
        self.assert_hold(retry_response)
        dispute_filter.assert_not_called()
        exception_filter.assert_not_called()

    def test_all_six_routes_still_require_authentication(self):
        requests = [
            (create_payment_intent, self.factory.post("/intents/", {}), {}),
            (
                payment_intent_status,
                self.factory.get("/intents/provider-secret/status/"),
                {"intent_id": "provider-secret"},
            ),
            (
                create_payment_method_setup,
                self.factory.post("/methods/setup/", {}),
                {"household_id": self.household_id},
            ),
            (
                detach_payment_method,
                self.factory.delete("/methods/71/"),
                {"household_id": self.household_id, "method_id": 71},
            ),
            (
                dispute_action_create,
                self.factory.post("/disputes/29/actions/", {}),
                {"dispute_id": 29},
            ),
            (
                payment_exception_retry,
                self.factory.post("/exceptions/37/retry/", {}),
                {"exception_id": 37},
            ),
        ]

        for view, request, kwargs in requests:
            with self.subTest(view=view.__name__):
                response = view(request, **kwargs)
                self.assertIn(response.status_code, {401, 403})
