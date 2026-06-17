from django.test import TestCase

from core.models import School
from households.models import Household
from payments.models import GatewayProvider, SavedPaymentMethod


class SavedPaymentMethodTests(TestCase):
    def test_create_saved_payment_method(self):
        school = School.objects.create(name="Payment Provider School")
        household = Household.objects.create(school_id=school.id, name="Family")

        row = SavedPaymentMethod.objects.create(
            school_id=school.id,
            household_id=household.id,
            provider=GatewayProvider.COMPUWERX,
            provider_customer_id="cust_1",
            provider_method_id="pm_123",
            brand="Visa",
            last4="4242",
            is_default=True,
        )
        self.assertEqual(row.provider_method_id, "pm_123")
        self.assertTrue(row.is_default)
