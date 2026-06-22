import pytest
from core.models import School
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


REMAINING_BATCH5_DASHBOARDS = [
    (
        'data-migration',
        [
            'Active Migration Jobs',
            'Records Migrated YTD',
            'Failed Records',
            'Validation Errors',
        ],
    ),
    (
        'integrations-automation',
        [
            'Active Integrations',
            'Sync Errors (Last 24h)',
            'Automations Running',
            'Last Successful Sync',
        ],
    ),
    (
        'revenue-operations',
        [
            'Total Revenue YTD',
            'Collections Rate',
            'Outstanding AR',
            'Revenue vs Budget',
        ],
    ),
    (
        'summer-camp',
        [
            'Registered Campers',
            'Staffed Sessions',
            'Waitlist Families',
            'Transport Confirmed',
        ],
    ),
    (
        'extended-care',
        [
            'Students Enrolled in After Care',
            'Check-Ins Today',
            'Outstanding Balances',
            'Staff On Duty Now',
        ],
    ),
    (
        'athletics-director',
        [
            'Active Varsity Programs',
            'Student Athletes',
            'Games This Week',
            'Eligibility Reviews Pending',
        ],
    ),
]


def _authed_client(username='batch5-remaining-dashboard-summary', *, school_id=None):
    user_model = get_user_model()
    user = user_model.objects.create_user(username=username, school_id=school_id)
    user.set_unusable_password()
    user.save(update_fields=['password'])
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
@pytest.mark.parametrize(('dashboard_key', 'expected_metric_labels'), REMAINING_BATCH5_DASHBOARDS)
def test_remaining_batch5_dashboard_serves_sample_payload_in_development(
    dashboard_key,
    expected_metric_labels,
):
    school = School.objects.create(name=f'{dashboard_key} home')
    client = _authed_client(
        f'batch5-{dashboard_key}-summary',
        school_id=school.id,
    )

    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': dashboard_key}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == dashboard_key
    assert data['meta']['school_id'] == str(school.id)
    assert data['meta']['served_from'] == 'sample'
    assert data['meta']['sample_payload_allowed'] is True
    assert [metric['label'] for metric in data['metrics']] == expected_metric_labels


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
@pytest.mark.parametrize(('dashboard_key', '_expected_metric_labels'), REMAINING_BATCH5_DASHBOARDS)
def test_remaining_batch5_dashboard_rejects_cross_tenant_access_for_non_staff_user(
    dashboard_key,
    _expected_metric_labels,
):
    school = School.objects.create(name=f'{dashboard_key} home')
    other_school = School.objects.create(name=f'{dashboard_key} other')
    client = _authed_client(
        f'batch5-{dashboard_key}-cross-tenant',
        school_id=school.id,
    )

    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': dashboard_key}),
        HTTP_X_SCHOOL_ID=str(other_school.id),
    )

    assert response.status_code == 404
    assert response.json()['detail'] == 'Not found.'


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
@pytest.mark.parametrize(('dashboard_key', '_expected_metric_labels'), REMAINING_BATCH5_DASHBOARDS)
def test_remaining_batch5_dashboard_requires_explicit_tenant_header(
    dashboard_key,
    _expected_metric_labels,
):
    client = _authed_client(f'batch5-{dashboard_key}-no-header')

    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': dashboard_key}),
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'X-School-Id header is required.'


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
@pytest.mark.parametrize(('dashboard_key', '_expected_metric_labels'), REMAINING_BATCH5_DASHBOARDS)
def test_remaining_batch5_dashboard_requires_authentication(
    dashboard_key,
    _expected_metric_labels,
):
    response = APIClient().get(
        reverse('dashboard-summary', kwargs={'dashboard_key': dashboard_key}),
    )

    assert response.status_code == 401
