from uuid import uuid4

from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import School


@override_settings(TENANT_HEADER_REQUIRED=True)
class TenantHeaderValidateSchoolTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_missing_header_returns_400(self):
        r = self.client.get("/api/v1/gradebook/sections/")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Missing required header", r.json().get("detail", ""))

    def test_invalid_uuid_returns_400(self):
        r = self.client.get("/api/v1/gradebook/sections/", HTTP_X_SCHOOL_ID="not-a-uuid")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Invalid X-School-Id", r.json().get("detail", ""))

    def test_unknown_uuid_returns_404(self):
        r = self.client.get("/api/v1/gradebook/sections/", HTTP_X_SCHOOL_ID=str(uuid4()))
        self.assertEqual(r.status_code, 404)
        self.assertIn("Unknown X-School-Id", r.json().get("detail", ""))

    def test_known_school_allows_request_past_middleware(self):
        # Create a real School so middleware accepts header.
        # We don't assert 200 because endpoint behavior may vary;
        # the key is: not blocked as 400/404 by middleware.
        s = School.objects.create(name="Test School")
        r = self.client.get("/api/v1/gradebook/sections/", HTTP_X_SCHOOL_ID=str(s.id))
        self.assertNotIn(r.status_code, (400, 404))
