from django.test import SimpleTestCase


class TestTenantsModuleSmoke(SimpleTestCase):
    def test_app_config_name(self):
        from tenants.apps import TenantsConfig

        self.assertEqual(TenantsConfig.name, "tenants")

    def test_tenant_context_importable(self):
        from tenants import tenant_context

        self.assertIsNotNone(tenant_context)
