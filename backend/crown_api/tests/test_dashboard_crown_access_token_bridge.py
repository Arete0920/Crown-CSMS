import pytest
from django.test import Client, override_settings

from sandbox_demo.services import create_sandbox_session


pytestmark = pytest.mark.django_db


@override_settings(TENANT_HEADER_REQUIRED=True, CROWN_ENV="development")
def test_dashboard_summary_accepts_valid_crown_token_bridge():
    session = create_sandbox_session(
        persona_key="school_admin",
        school_key_or_id="heritage-core",
        guidance="guided",
    )

    response = Client().get(
        "/api/v1/dashboards/school-administrator/summary",
        HTTP_AUTHORIZATION=f"Bearer {session['access']}",
        HTTP_X_SCHOOL_ID=session["school_id"],
    )

    assert response.status_code == 200
