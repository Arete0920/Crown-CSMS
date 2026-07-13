import pytest
from django.test import override_settings
from rest_framework.test import APIClient
from core.models import School, UserAccount


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True)
def test_dashboard_me_allows_dev_open_api_without_auth():
    client = APIClient()
    response = client.get('/api/dashboards/me/')
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True)
def test_dashboard_summary_allows_dev_open_api_without_auth():
    client = APIClient()
    response = client.get('/api/dashboards/summary/')
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True)
def test_dashboard_alerts_allows_dev_open_api_without_auth():
    client = APIClient()
    response = client.get('/api/dashboards/alerts/')
    assert response.status_code == 200


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True, CROWN_ENV='production')
def test_dev_open_does_not_bypass_tenant_in_production():
    client = APIClient()
    response = client.get('/api/dashboards/summary/')
    assert response.status_code in {400, 401}
    if response.status_code == 400:
        assert response.json().get('code') == 'missing_tenant'


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True, CROWN_ENV='production')
def test_production_mode_never_auto_creates_demo_school():
    client = APIClient()
    demo_school_id = '11111111-1111-1111-1111-111111111111'
    response = client.get('/api/dashboards/summary/', HTTP_X_SCHOOL_ID=demo_school_id)
    assert response.status_code in {401, 404}
    assert School.objects.filter(pk=demo_school_id).exists() is False


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True)
def test_invalid_tenant_header_fails_closed_even_in_dev_open():
    client = APIClient()
    response = client.get('/api/dashboards/summary/', HTTP_X_SCHOOL_ID='not-a-uuid')
    assert response.status_code == 400


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=False)
def test_cross_tenant_request_fails_for_non_staff_user():
    school_a = School.objects.create(name='School A')
    school_b = School.objects.create(name='School B')
    user = UserAccount.objects.create_user(
        username='tenant-user-a',
        email='tenant-user-a@example.com',
        password='test-pass-123',
        school=school_a,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get('/api/dashboards/me/', HTTP_X_SCHOOL_ID=str(school_b.id))
    assert response.status_code == 404


@pytest.mark.django_db
@override_settings(CROWN_DEV_OPEN_API=True)
def test_dev_open_does_not_bypass_staff_only_rbac():
    client = APIClient()
    response = client.get('/api/dashboards/dashboard-certification-center/summary')
    assert response.status_code == 401
