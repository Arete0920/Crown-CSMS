import pytest
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient

from crown_api.dashboards.models import DashboardSnapshot


@override_settings(TENANT_HEADER_REQUIRED=False)
@pytest.mark.django_db
def test_attendance_summary_serves_snapshot_first():
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

    client = APIClient()
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'attendance'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == 'attendance'
    assert data['meta']['served_from'] == 'snapshot'
    assert data['metrics'][0]['value'] == '97.0%'


@override_settings(TENANT_HEADER_REQUIRED=False)
@pytest.mark.django_db
def test_attendance_summary_falls_back_to_sample_payload():
    client = APIClient()
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'attendance'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == 'attendance'
    assert data['meta']['served_from'] == 'sample'
    assert len(data['metrics']) > 0


@override_settings(TENANT_HEADER_REQUIRED=False)
@pytest.mark.django_db
def test_unknown_dashboard_returns_404():
    client = APIClient()
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': 'does-not-exist'}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 404
    data = response.json()
    assert data['code'] == 'unknown_dashboard'
