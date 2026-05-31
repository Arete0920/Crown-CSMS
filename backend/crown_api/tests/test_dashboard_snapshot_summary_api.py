import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient

from crown_api.dashboards.models import DashboardSnapshot


def _authed_client(username='dashboard-summary-tester'):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username)
    user.set_unusable_password()
    user.save(update_fields=['password'])
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_attendance_summary_serves_snapshot_first_even_in_production():
    DashboardSnapshot.objects.create(
        school_id='heritage-demo',
        dashboard_key='attendance',
        source='seed',
        notes='test snapshot',
        payload={
            'dashboard_key': 'attendance',
            'metrics': [{'label': 'Present Rate Today', 'value': '97.0%'}],
            'alerts': [{'title': 'Snapshot Alert', 'level': 'High', 'secondary': 'snapshot'}],
            'queue': ['Snapshot queue item'],
            'meta': {'served_from': 'snapshot'},
        },
    )

    client = _authed_client('dashboard-summary-snapshot')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'attendance'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == 'attendance'
    assert data['meta']['served_from'] == 'snapshot'
    assert data['metrics'][0]['value'] == '97.0%'


@override_settings(
    TENANT_HEADER_REQUIRED=False,
    CROWN_ENV='development',
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False,
)
@pytest.mark.django_db
def test_attendance_summary_falls_back_to_sample_payload_in_non_production():
    client = _authed_client('dashboard-summary-nonprod')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'attendance'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == 'attendance'
    assert data['meta']['served_from'] == 'sample'
    assert data['meta']['sample_payload_allowed'] is True
    assert len(data['metrics']) > 0


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_attendance_summary_rejects_sample_payload_in_production_without_snapshot():
    client = _authed_client('dashboard-summary-prod-reject')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'attendance'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 503
    data = response.json()
    assert data['code'] == 'dashboard_live_data_required'
    assert data['dashboard_key'] == 'attendance'
    assert data['required_resolution']


@override_settings(
    TENANT_HEADER_REQUIRED=False,
    CROWN_ENV='production',
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=True,
)
@pytest.mark.django_db
def test_attendance_summary_allows_sample_payload_when_explicitly_enabled():
    client = _authed_client('dashboard-summary-prod-explicit')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'attendance'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == 'attendance'
    assert data['meta']['served_from'] == 'sample'
    assert data['meta']['sample_payload_allowed'] is True


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_unknown_dashboard_returns_404():
    client = _authed_client('dashboard-summary-unknown')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'does-not-exist'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 404
    data = response.json()
    assert data['code'] == 'unknown_dashboard'
