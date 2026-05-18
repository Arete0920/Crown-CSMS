import json

from django.test import RequestFactory, SimpleTestCase

from solomon.apps import SolomonConfig
from solomon.views import solomon_status


class SolomonScaffoldTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_app_config_name(self):
        self.assertEqual(SolomonConfig.name, "solomon")

    def test_solomon_status_returns_200(self):
        request = self.factory.get("/status/")
        response = solomon_status(request)

        self.assertEqual(response.status_code, 200)

    def test_solomon_status_payload(self):
        request = self.factory.get("/status/")
        response = solomon_status(request)
        payload = json.loads(response.content)

        self.assertEqual(payload.get("module"), "solomon")
        self.assertEqual(payload.get("status"), "scaffold")
        self.assertEqual(payload.get("implementation"), "not_started")
