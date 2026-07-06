from django.test import TestCase
from django.test.client import RequestFactory
from django.http import HttpResponse
from rest_framework.test import APIClient

from crown_api.auth_middleware import JwtAuthMiddleware
from sandbox_demo.services import create_sandbox_session


class CrownAccessDrfAuthTests(TestCase):
    def test_crown_access_token_authenticates_dashboard_summary_apiview(self):
        session = create_sandbox_session(
            persona_key="school_admin",
            school_key_or_id="heritage-core",
            guidance="guided",
        )

        client = APIClient()
        response = client.get(
            "/api/v1/dashboards/school-administrator/summary",
            HTTP_AUTHORIZATION=f"Bearer {session['access']}",
            HTTP_X_SCHOOL_ID=session["school_id"],
        )

        self.assertEqual(response.status_code, 200)

    def test_middleware_clears_authorization_after_crown_authentication(self):
        session = create_sandbox_session(
            persona_key="school_admin",
            school_key_or_id="heritage-core",
            guidance="guided",
        )
        request = RequestFactory().get(
            "/api/v1/dashboards/school-administrator/summary",
            HTTP_AUTHORIZATION="Bearer " + session["access"],
        )
        captured = {}

        def get_response(incoming_request):
            captured["authorization"] = incoming_request.META.get("HTTP_AUTHORIZATION")
            return HttpResponse(status=204)

        response = JwtAuthMiddleware(get_response)(request)

        self.assertEqual(response.status_code, 204)
        self.assertIsNone(captured["authorization"])
        self.assertIsNotNone(getattr(request, "_crown_authenticated", None))
