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


def _secure_get(client, *args, **kwargs):
    """Exercise dashboard routes as HTTPS in production-like test contexts."""
    kwargs.setdefault("secure", True)
    return client.get(*args, **kwargs)


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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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

    response = _secure_get(client, 
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
def test_implementation_success_summary_serves_sample_payload_in_development():
    school = School.objects.create(name="Implementation Success Home")
    client = _authed_client(
        "dashboard-summary-batch5-implementation-success",
        school_id=school.id,
    )
    response = _secure_get(client, 
        reverse(
            "dashboard-summary", kwargs={"dashboard_key": "implementation-success"}
        ),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "implementation-success"
    assert data["meta"]["served_from"] == "sample"
    assert data["meta"]["sample_payload_allowed"] is True
    assert [metric["label"] for metric in data["metrics"]] == [
        "Schools in Active Onboarding",
        "Go-Lives This Quarter",
        "Open Implementation Tickets",
        "Avg Onboarding Days",
    ]


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_implementation_success_summary_allows_same_tenant_access():
    school = School.objects.create(name="Implementation Success Same Tenant")
    client = _authed_client(
        "dashboard-summary-batch5-implementation-success-same-tenant",
        school_id=school.id,
    )

    response = _secure_get(client, 
        reverse(
            "dashboard-summary", kwargs={"dashboard_key": "implementation-success"}
        ),
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_key"] == "implementation-success"
    assert data["meta"]["school_id"] == str(school.id)
    assert data["meta"]["served_from"] == "sample"


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_implementation_success_summary_rejects_cross_tenant_access_for_non_staff_user():
    school = School.objects.create(name="Implementation Success Home")
    other_school = School.objects.create(name="Implementation Success Other")
    client = _authed_client(
        "dashboard-summary-batch5-implementation-success-cross-tenant",
        school_id=school.id,
    )

    response = _secure_get(client, 
        reverse(
            "dashboard-summary", kwargs={"dashboard_key": "implementation-success"}
        ),
        HTTP_X_SCHOOL_ID=str(other_school.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_master_control_summary_rejects_cross_tenant_access_for_non_staff_user():
    school = School.objects.create(name="Master Control Home")
    other_school = School.objects.create(name="Master Control Other")
    client = _authed_client(
        "dashboard-summary-batch5-master-control-cross-tenant",
        school_id=school.id,
    )

    response = _secure_get(client, 
        reverse("dashboard-summary", kwargs={"dashboard_key": "master-control"}),
        HTTP_X_SCHOOL_ID=str(other_school.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_implementation_success_summary_requires_authentication():
    client = APIClient()
    response = _secure_get(client, 
        reverse(
            "dashboard-summary", kwargs={"dashboard_key": "implementation-success"}
        ),
    )

    assert response.status_code == 401


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_implementation_success_summary_requires_explicit_tenant_header():
    client = _authed_client("dashboard-summary-batch5-implementation-success-no-header")
    response = _secure_get(client, 
        reverse(
            "dashboard-summary", kwargs={"dashboard_key": "implementation-success"}
        ),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "X-School-Id header is required."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_requires_explicit_tenant_header():
    client = _authed_client("dashboard-summary-batch0-compliance-audit-no-header")
    response = _secure_get(client, 
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "X-School-Id header is required."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_rejects_invalid_tenant_header():
    client = _authed_client("dashboard-summary-batch0-compliance-audit-invalid-header")
    response = _secure_get(client, 
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
        HTTP_X_SCHOOL_ID="not-a-uuid",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid X-School-Id (must be a UUID)."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_compliance_audit_summary_rejects_nonexistent_school():
    client = _authed_client("dashboard-summary-batch0-compliance-audit-missing-school")
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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

    response = _secure_get(client, 
        reverse("dashboard-summary", kwargs={"dashboard_key": "compliance-audit"}),
        HTTP_X_SCHOOL_ID=str(school_b.id),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Not found."


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="development")
@pytest.mark.django_db
def test_dashboard_certification_center_staff_user_receives_summary_payload():
    client = _authed_client("dashboard-cert-center-staff", is_staff=True)
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
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
    response = _secure_get(client, 
        reverse("dashboard-summary", kwargs={"dashboard_key": dashboard_key}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 401


@override_settings(TENANT_HEADER_REQUIRED=False, CROWN_ENV="production")
@pytest.mark.django_db
def test_unknown_dashboard_returns_404():
    client = _authed_client("dashboard-summary-unknown")
    response = _secure_get(client, 
        reverse("dashboard-summary", kwargs={"dashboard_key": "does-not-exist"}),
        HTTP_X_SCHOOL_ID="heritage-demo",
    )

    assert response.status_code == 404
    data = response.json()
    assert data["code"] == "unknown_dashboard"


def test_sandbox_ready_workflow_runs_on_dashboard_pull_requests():
    from pathlib import Path

    workflow = (
        Path(__file__).resolve().parents[3]
        / ".github"
        / "workflows"
        / "sandbox-ready-evidence.yml"
    ).read_text(encoding="utf-8")
    assert "pull_request:" in workflow
    assert '"backend/crown_api/tests/test_dashboard_snapshot_summary_api.py"' in workflow
    assert '".github/workflows/sandbox-ready-evidence.yml"' in workflow
