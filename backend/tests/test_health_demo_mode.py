import os
from django.test import TestCase, Client

class HealthDemoModeEnvTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_demo_mode_true_when_env_true(self):
        os.environ["CROWN_DEMO_MODE"] = "true"
        r = self.client.get("/api/health/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("demo_mode", data)
        self.assertIs(data["demo_mode"], True)

    def test_demo_mode_false_when_env_missing(self):
        os.environ.pop("CROWN_DEMO_MODE", None)
        r = self.client.get("/api/health/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("demo_mode", data)
        self.assertIs(data["demo_mode"], False)
