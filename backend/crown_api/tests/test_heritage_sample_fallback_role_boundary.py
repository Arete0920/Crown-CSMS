import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings

from core.models import School, UserRole
from crown_api.dashboards.views import _sample_dashboard_payloads_allowed
from sandbox_demo.catalog import DEMO_SCHOOL_ID


User = get_user_model()


def _request_for(user, demo_role=None, school_id=DEMO_SCHOOL_ID):
    headers = {"HTTP_X_SCHOOL_ID": school_id}
    if demo_role is not None:
        headers["HTTP_X_DEMO_ROLE"] = demo_role
    request = RequestFactory().get(
        "/api/v1/dashboards/admin/summary/",
        **headers,
    )
    request.user = user
    return request


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_heritage_fallback_uses_server_side_role_without_demo_role_header():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    user = User.objects.create_user(
        username="heritage-admin-role-boundary@example.org",
        email="heritage-admin-role-boundary@example.org",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")

    assert _sample_dashboard_payloads_allowed(_request_for(user)) is True


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_forged_demo_role_header_cannot_change_sample_authority():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    user = User.objects.create_user(
        username="heritage-teacher-role-boundary@example.org",
        email="heritage-teacher-role-boundary@example.org",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="TEACHER")

    baseline = _sample_dashboard_payloads_allowed(_request_for(user))
    forged_admin = _sample_dashboard_payloads_allowed(_request_for(user, "school_admin"))
    forged_unknown = _sample_dashboard_payloads_allowed(_request_for(user, "unknown_persona"))

    assert baseline is True
    assert forged_admin is baseline
    assert forged_unknown is baseline


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_heritage_fallback_rejects_user_without_assigned_persona_role_even_with_forged_header():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    user = User.objects.create_user(
        username="heritage-no-role@example.org",
        email="heritage-no-role@example.org",
        school=school,
    )

    assert _sample_dashboard_payloads_allowed(_request_for(user)) is False
    assert _sample_dashboard_payloads_allowed(_request_for(user, "school_admin")) is False


@override_settings(CROWN_ENV="production", CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False)
@pytest.mark.django_db
def test_heritage_fallback_rejects_cross_school_request_even_with_valid_server_role():
    school = School.objects.create(id=DEMO_SCHOOL_ID, name="Heritage Christian Academy")
    other_school = School.objects.create(name="Other School")
    user = User.objects.create_user(
        username="heritage-cross-school@example.org",
        email="heritage-cross-school@example.org",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")

    assert (
        _sample_dashboard_payloads_allowed(
            _request_for(user, "school_admin", school_id=str(other_school.id))
        )
        is False
    )
