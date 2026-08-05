import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings

from core.models import School, UserRole
from crown_api.dashboards.views import _sample_dashboard_payloads_allowed
from sandbox_demo.catalog import DEMO_SCHOOL_ID


User = get_user_model()


def _request_for(user, demo_role):
    request = RequestFactory().get(
        "/api/v1/dashboards/admin/summary/",
        HTTP_X_DEMO_ROLE=demo_role,
        HTTP_X_SCHOOL_ID=DEMO_SCHOOL_ID,
    )
    request.user = user
    return request


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_heritage_fallback_requires_header_persona_to_match_assigned_role():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    user = User.objects.create_user(
        username="heritage-admin-role-boundary@example.org",
        email="heritage-admin-role-boundary@example.org",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")

    assert _sample_dashboard_payloads_allowed(_request_for(user, "school_admin")) is True
    assert _sample_dashboard_payloads_allowed(_request_for(user, "teacher")) is False
    assert _sample_dashboard_payloads_allowed(_request_for(user, "unknown_persona")) is False


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_heritage_fallback_rejects_user_without_assigned_persona_role():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    user = User.objects.create_user(
        username="heritage-no-role@example.org",
        email="heritage-no-role@example.org",
        school=school,
    )

    assert _sample_dashboard_payloads_allowed(_request_for(user, "school_admin")) is False
