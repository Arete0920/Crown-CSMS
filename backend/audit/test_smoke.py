from django.test import SimpleTestCase


class TestAuditModuleSmoke(SimpleTestCase):
    def test_app_config_name(self):
        from audit.apps import AuditConfig

        self.assertEqual(AuditConfig.name, "audit")

    def test_models_importable(self):
        from audit import models

        self.assertIsNotNone(models)
