from django.test import TestCase
from rest_framework.test import APIClient

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
