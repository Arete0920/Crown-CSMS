from django.test import TestCase

from core.models import School
from payments.models import GatewayProvider, PaymentSupportException


class PaymentSupportExceptionTests(TestCase):
    def test_create_exception(self):
        school = School.objects.create(name="Compuwerx School")

        row = PaymentSupportException.objects.create(
            school_id=school.id,
            provider=GatewayProvider.COMPUWERX,
            category="gateway_event_processing",
            severity="error",
            message="Sample error",
        )
        self.assertEqual(row.category, "gateway_event_processing")
