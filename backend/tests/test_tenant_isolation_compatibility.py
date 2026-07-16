from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from core.middleware import TenantIsolationMiddleware
from core.models import School


User = get_user_model()


class TenantIsolationCompatibilityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.school = School.objects.create(name="Compatibility School")
        self.user = User.objects.create_user(
            username="compat-user",
            email="compat-user@example.com",
            password="test-password",
            school=self.school,
        )

    def test_legacy_layer_delegates_to_canonical_user_school_resolution(self):
        request = self.factory.get("/api/v1/test/")
        request.user = self.user

        TenantIsolationMiddleware(lambda req: None).process_request(request)

        self.assertEqual(request.crown_tenant.school_id, self.school.id)
        self.assertEqual(request.crown_tenant.source, "user")
        self.assertEqual(request.tenant_school_id, self.school.id)
        self.assertFalse(hasattr(request, "school"))

    def test_existing_canonical_context_is_not_replaced(self):
        request = self.factory.get("/api/v1/test/")
        request.user = self.user

        middleware = TenantIsolationMiddleware(lambda req: None)
        middleware.process_request(request)
        original = request.crown_tenant
        middleware.process_request(request)

        self.assertIs(request.crown_tenant, original)
