"""
Release Reliability Dashboard — API permission and tenant behavior proof.

Closes: tcmegahan/Crown2026#1111

Proof scope:
  1. Authentication required — unauthenticated → 401.
  2. Authenticated user receives 200 with contract-compliant payload shape.
  3. Sample payload carries required contract fields (dashboard_key, metrics,
     alerts, queue, meta) in development.
  4. Snapshot record takes priority over sample payload in all environments.
  5. Production environment without snapshot returns 503 (live data required).
  6. Tenant header accepted — school_id is recorded in response meta.
  7. Tenant isolation note: cross-tenant enforcement is not yet wired for this
     dashboard in the current view layer (documented gap, not a pass claim).

Non-claims:
  This file does not certify the dashboard.
  This file does not approve sandbox, pilot, production, or release GO.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from crown_api.dashboards.models import DashboardSnapshot

DASHBOARD_KEY = 'release-reliability'

User = get_user_model()


def _authed_client(username, *, is_staff=False, is_superuser=False):
    user = User.objects.create_user(
        username=username,
        is_staff=is_staff,
        is_superuser=is_superuser,
    )
    user.set_unusable_password()
    user.save(update_fields=['password'])
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ---------------------------------------------------------------------------
# 1. Authentication — unauthenticated request must be rejected
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_release_reliability_summary_rejects_unauthenticated_request():
    """Unauthenticated callers must receive 401."""
    client = APIClient()
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# 2. Authenticated user receives 200 in development
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_release_reliability_summary_returns_200_for_authenticated_user():
    """Authenticated user with school header receives HTTP 200."""
    client = _authed_client('rr-proof-auth')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# 3. Payload shape — required contract fields present
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_release_reliability_sample_payload_has_contract_fields():
    """Sample payload carries dashboard_key, metrics, alerts, queue, meta."""
    client = _authed_client('rr-proof-shape')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )
    assert response.status_code == 200
    data = response.json()

    assert data.get('dashboard_key') == DASHBOARD_KEY
    assert isinstance(data.get('metrics'), list)
    assert len(data['metrics']) > 0
    assert isinstance(data.get('alerts'), list)
    assert isinstance(data.get('queue'), list)
    assert isinstance(data.get('meta'), dict)


# ---------------------------------------------------------------------------
# 4. Metric labels present — release-specific KPIs
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_release_reliability_sample_payload_has_release_kpis():
    """Sample payload exposes expected release KPI labels."""
    client = _authed_client('rr-proof-kpis')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )
    assert response.status_code == 200
    data = response.json()

    metric_labels = [m['label'] for m in data['metrics']]
    assert any('Deployment' in lbl or 'deployment' in lbl for lbl in metric_labels), (
        f"Expected a deployment-count metric; got {metric_labels}"
    )
    assert any('Incident' in lbl or 'incident' in lbl for lbl in metric_labels), (
        f"Expected an incident metric; got {metric_labels}"
    )


# ---------------------------------------------------------------------------
# 5. Sample payload source flag
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_release_reliability_development_payload_is_served_from_sample():
    """Development environment response reports served_from=sample."""
    client = _authed_client('rr-proof-sample-flag')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['meta']['served_from'] == 'sample'
    assert data['meta']['sample_payload_allowed'] is True


# ---------------------------------------------------------------------------
# 6. Snapshot priority — snapshot record beats sample in all environments
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_release_reliability_snapshot_takes_priority_over_sample_in_production():
    """A seeded DashboardSnapshot is served first, even in production."""
    DashboardSnapshot.objects.create(
        school_id='heritage-demo',
        dashboard_key=DASHBOARD_KEY,
        source='seed',
        notes='Proof snapshot for release-reliability truth-alignment.',
        payload={
            'dashboard_key': DASHBOARD_KEY,
            'metrics': [{'label': 'Deployments This Month', 'value': '9'}],
            'alerts': [{'title': 'Proof alert', 'level': 'Low', 'secondary': 'test'}],
            'queue': ['Verify proof snapshot'],
            'meta': {'served_from': 'snapshot', 'certification_candidate': 'hybrid'},
        },
    )

    client = _authed_client('rr-proof-snapshot-priority')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 200
    data = response.json()
    assert data['dashboard_key'] == DASHBOARD_KEY
    assert data['meta']['served_from'] == 'snapshot'
    assert data['metrics'][0]['value'] == '9'


# ---------------------------------------------------------------------------
# 7. Production gate — no snapshot → 503
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='production')
@pytest.mark.django_db
def test_release_reliability_production_without_snapshot_returns_503():
    """Production environment without a snapshot returns 503 live-data-required."""
    client = _authed_client('rr-proof-prod-gate')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )

    assert response.status_code == 503
    data = response.json()
    assert data['code'] == 'dashboard_live_data_required'
    assert data['dashboard_key'] == DASHBOARD_KEY
    assert 'required_resolution' in data


# ---------------------------------------------------------------------------
# 8. Tenant header — school_id recorded in meta
# ---------------------------------------------------------------------------

@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV='development')
@pytest.mark.django_db
def test_release_reliability_tenant_header_recorded_in_meta():
    """X-School-Id header value is reflected in the response meta.school_id."""
    client = _authed_client('rr-proof-tenant-meta')
    response = client.get(
        reverse('dashboard-summary', kwargs={'dashboard_key': DASHBOARD_KEY}),
        HTTP_X_SCHOOL_ID='heritage-demo',
    )
    assert response.status_code == 200
    data = response.json()
    assert data['meta']['school_id'] == 'heritage-demo'
