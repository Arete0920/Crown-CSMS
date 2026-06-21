import pytest
from core.models import School
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import override_settings
from rest_framework.test import APIClient

from crown_api.dashboards.models import DashboardSnapshot


def _authed_client(
    username="dashboard-summary-tester",
    *,
    is_staff=False,
    is_superuser=False,
    school_id=None,
):
    user_model = get_user_model()
    user = user_model.objects.create_user(
        username=username,
        is_staff=is_staff,
        is_superuser=is_superuser,
        school_id=school_id,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_attendance_summary_serves_snapshot_first_even_in_production():
    DashboardSnapshot.objects.create(
        school_id="heritage-demo",
        dashboard_key="attendance",
        source="seed",
        notes="test snapshot",
        payload={
            "dashboard_key": "attendance",
            "metrics": [{"label": "Present Rate Today", "value": "97.0%"}],
            "alerts": [
                {"title": "Snapshot Alert", "level": "High", "secondary": "snapshot"}
            ],
            "queue": ["Snapshot queue item"],
            "meta": {"served_from": "snapshot"},
        },
    )

    client = _authed_client("dashboard-summary-snapshot")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "attendance"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "attendance"
    assert data["meta"]["served_from"] == "snapshot"
    assert data["metrics"][0]["value"] == "97.0%"


@override_settings(
    TENANT_HEADER_REQUIRED=False,
    CROWN_ENV="development",
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=False,
)
@pytest.mark.django_db
def test_attendance_summary_falls_back_to_sample_payload_in_non_production():
    client = _authed_client("dashboard-summary-nonprod")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "attendance"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "attendance"
    assert data["meta"]["served_from"] == "sample"
    assert data["meta"]["sample_payload_allowed"] is True
    assert len(data["metrics"]) > 0


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_attendance_summary_rejects_sample_payload_in_production_without_snapshot():
    client = _authed_client("dashboard-summary-prod-reject")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "attendance"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "dashboard_live_data_required"
    assert data["dashboard_key"] == "attendance"
    assert data["required_resolution"]


@override_settings(
    TENANT_HEADER_REQUIRED=False,
    CROWN_ENV="production",
    CROWN_ALLOW_SAMPLE_DASHBOARD_PAYLOADS=True,
)
@pytest.mark.django_db
def test_attendance_summary_allows_sample_payload_when_explicitly_enabled():
    client = _authed_client("dashboard-summary-prod-explicit")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "attendance"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "attendance"
    assert data["meta"]["served_from"] == "sample"
    assert data["meta"]["sample_payload_allowed"] is True


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "dashboard_key",
    ["release-reliability"],
)
def test_batch0_school_scoped_summary_routes_serve_sample_payloads_in_development(
    dashboard_key,
):
    client = _authed_client(f"dashboard-summary-batch0-{dashboard_key}")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": dashboard_key}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == dashboard_key
    assert data["meta"]["served_from"] == "sample"
    assert len(data["metrics"]) > 0


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_master_control_summary_serves_sample_payload_in_development():
    school = School.objects.create(name="Master Control Development")
    client = _authed_client(
        "dashboard-summary-batch5-master-control",
        school_id=school.id,
    )
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "master-control"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "master-control"
    assert data["meta"]["served_from"] == "sample"
    assert data["meta"]["sample_payload_allowed"] is True
    assert [metric["label"] for metric in data["metrics"]] == [
        "Platform Uptime (30d)",
        "Active Tenants",
        "Open Support Tickets",
        "Pending Data Migrations",
    ]


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_master_control_summary_requires_authentication():
    client = APIClient()
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "master-control"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 401


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_master_control_summary_allows_same_tenant_access():
    school = School.objects.create(name="Master Control Home")
    client = _authed_client(
        "dashboard-summary-batch5-master-control-same-tenant",
        school_id=school.id,
    )

    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "master-control"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "master-control"
    assert data["meta"]["school_id"] == str(school.id)
    assert data["meta"]["served_from"] == "sample"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_master_control_summary_rejects_cross_tenant_access_for_non_staff_user():
    school = School.objects.create(name="Master Control Home")
    other_school = School.objects.create(name="Master Control Other")
    client = _authed_client(
        "dashboard-summary-batch5-master-control-cross-tenant",
        school_id=school.id,
    )

    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "master-control"}),
        HTTP_X_SCHOOL_ID=str(other_school.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_requires_explicit_tenant_header():
    client = _authed_client("dashboard-summary-batch0-compliance-audit-no-header")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "X-School-Id header is required."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_rejects_invalid_tenant_header():
    client = _authed_client("dashboard-summary-batch0-compliance-audit-invalid-header")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
        HTTP_X_SCHOOL_ID="not-a-uuid",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid X-School-Id (must be a UUID)."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_rejects_nonexistent_school():
    client = _authed_client("dashboard-summary-batch0-compliance-audit-missing-school")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
        HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000000",
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "School not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_serves_sample_payload_for_request_school():
    school = School.objects.create(name="Heritage Demo")
    client = _authed_client("dashboard-summary-batch0-compliance-audit-allowed")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "compliance-audit"
    assert [metric["label"] for metric in data["metrics"]] == [
        "Open Compliance Items",
        "Audits Completed This Year",
        "Policies Reviewed",
        "Training Completion Rate",
    ]
    assert data["meta"]["served_from"] == "sample"
    assert data["meta"]["sample_payload_allowed"] is True
    assert data["meta"]["certification_candidate"] == "hybrid"
    assert (
        data["meta"]["truth_source"]
        == "backend/crown_api/dashboards/sample_payloads.py:compliance_audit_sample_payload"
    )
    assert data["meta"]["school_id"] == str(school.id)


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_blocks_cross_tenant_access():
    school_a = School.objects.create(name="Tenant A")
    school_b = School.objects.create(name="Tenant B")
    client = _authed_client(
        "dashboard-summary-batch0-compliance-audit-cross-tenant",
        school_id=school_a.id,
    )

    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_dashboard_certification_center_staff_user_receives_summary_payload():
    client = _authed_client("dashboard-cert-center-staff", is_staff=True)
    response = client.get(
        reverse(
            "dashboard-summary",
            kwargs={"dashboard_key": "dashboard-certification-center"},
        ),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "dashboard-certification-center"
    assert data["meta"]["served_from"] == "sample"
    assert data["meta"]["sample_payload_allowed"] is True


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_dashboard_certification_center_non_staff_user_is_forbidden():
    client = _authed_client("dashboard-cert-center-non-staff")
    response = client.get(
        reverse(
            "dashboard-summary",
            kwargs={"dashboard_key": "dashboard-certification-center"},
        ),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Forbidden."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_dashboard_certification_center_superuser_receives_summary_payload():
    client = _authed_client("dashboard-cert-center-superuser", is_superuser=True)
    response = client.get(
        reverse(
            "dashboard-summary",
            kwargs={"dashboard_key": "dashboard-certification-center"},
        ),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "dashboard-certification-center"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
@pytest.mark.parametrize(
    "dashboard_key",
    ["dashboard-certification-center", "release-reliability", "compliance-audit"],
)
def test_batch0_summary_routes_require_authentication(dashboard_key):
    client = APIClient()
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": dashboard_key}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 401


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_unknown_dashboard_returns_404():
    client = _authed_client("dashboard-summary-unknown")
    response = client.get(
        reverse("dashboard-summary", kwargs={"dashboard_key": "does-not-exist"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "unknown_dashboard"
