from django.test import TestCase, override_settings
from rest_framework.test import APIClient

class TenantHeaderRequiredTests(TestCase):

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_health_exempt_no_header(self):
        c = APIClient()
        r = c.get('/api/v1/health/')
        self.assertNotEqual(r.status_code, 400)

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_auth_exempt_no_header(self):
        c = APIClient()
        r = c.post('/api/v1/auth/token/', {})
        # Auth view may return 400 for missing credentials, but NOT the
        # middleware's "Missing required header: X-School-Id" error.
        self.assertNotIn(b"X-School-Id", r.content)

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_other_api_requires_header(self):
        c = APIClient()
        r = c.get('/api/v1/academics/courses/')
        self.assertEqual(r.status_code, 400)
        self.assertIn("X-School-Id", str(r.content))

    @override_settings(TENANT_HEADER_REQUIRED=True)
    def test_options_request_no_header_allowed(self):
        """CORS preflight OPTIONS requests must pass without X-School-Id header"""
        c = APIClient()
        r = c.options('/api/v1/academics/courses/')
        # Should NOT return 400 for missing header (CORS preflight must work)
        self.assertNotEqual(r.status_code, 400, "OPTIONS request blocked by middleware")
