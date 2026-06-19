import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from crown_api.dashboards.models import DashboardSnapshot


DASHBOARD_KEY = 'dashboard-certification-center'


def _authed_client(username='dashboard-cert-center-proof', *, is_staff=False, is_superuser=False):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    user.set_unusable_password()
    user.save(update_fields=['password'])

    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _summary_url():
    return reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY})


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_certification_center_staff_receives_snapshot_not_sample_in_production():
    DashboardSnapshot.objects.create(
        school_id='heritage-demo',
        dashboard_key=DASHBOARD_KEY,
        source='dashboard-certification-state-register',
        notes='first dashboard certification proof candidate',
        payload={
            'dashboard_key': DASHBOARD_KEY,
            'metrics': [
                {'label': 'Dashboards Certified', 'value': '0'},
                {'label': 'Mapped Only', 'value': '40'},
                {'label': 'Cert Rate', 'value': '0%'},
            ],
            'alerts': [
                {
                    'title': 'No dashboards are certified yet',
                    'level': 'High',
                    'secondary': 'Snapshot truth comes from the dashboard certification state register.',
                }
            ],
            'queue': [
                'Assign independent reviewer',
                'Attach tenant and browser role proof',
                'Promote matrix row only after review',
            ],
            'meta': {
                'served_from': 'snapshot',
                'source_register': 'audit-artifacts/dashboard-completion/state/dashboard-certification-state.json',
            },
        },
    )

    client = _authed_client('dashboard-cert-center-prod-staff', is_staff=True)
    response = client.get(_summary_url(), HTTP_X_SCHOOL_ID='heritage-demo')

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == DASHBOARD_KEY
    assert data['meta']['served_from'] == 'snapshot'
    assert data['meta']['snapshot_source'] == 'dashboard-certification-state-register'
    assert data['meta']['school_id'] == 'heritage-demo'
    assert 'sample_payload_allowed' not in data['meta']
    assert data['metrics'][0]['label'] == 'Dashboards Certified'


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_certification_center_production_rejects_sample_when_snapshot_missing():
    client = _authed_client('dashboard-cert-center-prod-no-snapshot', is_staff=True)
    response = client.get(_summary_url(), HTTP_X_SCHOOL_ID='heritage-demo')

    assert response.status_code == 503
    data = response.json()
    assert data['code'] == 'dashboard_live_data_required'
    assert data['dashboard_key'] == DASHBOARD_KEY
    assert data['school_id'] == 'heritage-demo'
    assert data['required_resolution']


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_certification_center_does_not_leak_other_school_snapshot():
    DashboardSnapshot.objects.create(
        school_id='school-a',
        dashboard_key=DASHBOARD_KEY,
        source='school-a-certification-state-register',
        payload={
            'dashboard_key': DASHBOARD_KEY,
            'metrics': [{'label': 'School A Only', 'value': 'secret'}],
            'alerts': [],
            'queue': [],
            'meta': {'served_from': 'snapshot'},
        },
    )

    client = _authed_client('dashboard-cert-center-prod-school-b', is_staff=True)
    response = client.get(_summary_url(), HTTP_X_SCHOOL_ID='school-b')

    assert response.status_code == 503
    data = response.json()
    assert data['code'] == 'dashboard_live_data_required'
    assert data['school_id'] == 'school-b'
    assert 'School A Only' not in str(data)
    assert 'secret' not in str(data)


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_certification_center_non_staff_forbidden_even_with_school_header():
    client = _authed_client('dashboard-cert-center-dev-nonstaff')
    response = client.get(_summary_url(), HTTP_X_SCHOOL_ID='heritage-demo')

    assert response.status_code == 403
    assert response.json()['detail'] == 'Forbidden.'


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_certification_center_requires_authentication():
    client = APIClient()
    response = client.get(_summary_url(), HTTP_X_SCHOOL_ID='heritage-demo')

    assert response.status_code == 401
