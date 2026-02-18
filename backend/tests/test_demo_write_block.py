from django.test import override_settings
from rest_framework.test import APIClient
from django.test import TestCase

class DemoWriteBlockTests(TestCase):

    @override_settings(CROWN_DEMO_MODE=True)
    def test_post_blocked_in_demo_mode(self):
        client = APIClient()
        response = client.post('/api/v1/academics/courses/', {})
        self.assertEqual(response.status_code, 403)

    @override_settings(CROWN_DEMO_MODE=True)
    def test_auth_endpoint_exempt_in_demo_mode(self):
        client = APIClient()
        response = client.post('/api/dev/token/', {})
        # Should NOT be 403 — auth is exempt from write block
        self.assertNotEqual(response.status_code, 403)
