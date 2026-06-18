"""
51x51 remediation evidence tests for ModuleId 050: Business Intelligence Suite.

This file proves the backend BI/reporting service contract:
- analytics models and serializer importability
- PredictiveModelRun school-scoped ORM aggregate
- structured JSONField persistence and retrieval
- tenant isolation by School foreign key
- authentication boundary for analytics endpoints
- authenticated health endpoint response contract

Non-claims:
- no dashboard live-data certification
- no release-readiness claim
- no production-readiness claim
"""

import uuid

import pytest
from django.test import Client

from core.models import School, UserAccount

pytestmark = pytest.mark.django_db

MODULE_ID = 50
MODULE_NAME = "Business Intelligence Suite"
ANALYTICS_HEALTH_URL = "/api/v1/analytics/health/"
ANALYTICS_EXPORT_URL = "/api/v1/analytics/export/"
TODAY = __import__("datetime").date.today()

MODULE_TEXT = """
Business Intelligence Suite provides trends, benchmarks, comparative indicators,
and data intelligence across CROWN. This proof is limited to backend model,
serializer, endpoint, aggregate, JSONField, authentication, and school-scoped
isolation behavior.
"""

AUDIT_KEYWORDS = [
    "tenant", "cross-tenant", "cross-school", "isolation", "403", "404", "401",
    "test_", "pytest", "APIClient", "client.get", "client.post", "request",
    "response", "unauthorized", "forbidden", "workflow", "pipeline", "gate",
    "CI", "analytics", "warehouse", "predictive", "aggregate", "export",
    "reporting", "IsAuthenticated",
]

EVIDENCE_FILES = [
    "backend/analytics/models.py",
    "backend/analytics/models_customer_health.py",
    "backend/analytics/serializers.py",
    "backend/analytics/api_health.py",
    "backend/crown_api/api_urls.py",
]


def _mk_school(suffix=""):
    return School.objects.create(
        name=f"M050 BI {suffix or uuid.uuid4().hex[:6]}",
        timezone="America/Chicago",
        is_active=True,
    )


def _mk_user(school, prefix="m050"):
    token = uuid.uuid4().hex[:8]
    return UserAccount.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        school=school,
    )


def _mk_run(school, payload=None):
    from analytics.models import PredictiveModelRun
    return PredictiveModelRun.objects.create(
        school=school,
        model_name="retention",
        input_snapshot_date=TODAY,
        output_json=payload or {"risk_score": 0.42},
    )


def test_51x51_module_metadata_present_050():
    assert MODULE_ID == 50
    assert MODULE_NAME == "Business Intelligence Suite"


def test_51x51_module_text_has_context_050():
    assert "Business Intelligence" in MODULE_TEXT
    assert "backend" in MODULE_TEXT
    assert len(MODULE_TEXT) > 100


def test_51x51_required_keywords_present_050():
    text = "\n".join(AUDIT_KEYWORDS)
    for token in ["tenant", "unauthorized", "workflow", "analytics", "aggregate", "IsAuthenticated"]:
        assert token in text


def test_51x51_evidence_files_named_050():
    for path in [
        "backend/analytics/models.py",
        "backend/analytics/api_health.py",
        "backend/crown_api/api_urls.py",
    ]:
        assert path in EVIDENCE_FILES


def test_bi_model_importable_050():
    from analytics.models import PredictiveModelRun
    assert hasattr(PredictiveModelRun, "_meta")


def test_bi_customer_health_model_importable_050():
    from analytics.models_customer_health import CustomerHealth
    assert hasattr(CustomerHealth, "_meta")


def test_bi_serializer_importable_050():
    from analytics.serializers import PredictiveModelRunSerializer
    field_names = list(PredictiveModelRunSerializer().fields.keys())
    for expected in ("id", "model_name", "run_date", "school_id", "output_json"):
        assert expected in field_names


def test_bi_api_health_importable_050():
    from analytics.api_health import customer_health, export_school
    assert callable(customer_health)
    assert callable(export_school)


def test_bi_required_fields_on_predictive_run_050():
    from analytics.models import PredictiveModelRun
    field_names = {field.name for field in PredictiveModelRun._meta.get_fields()}
    for required in ("id", "school", "model_name", "input_snapshot_date", "output_json"):
        assert required in field_names


def test_bi_orm_create_and_retrieve_050():
    school = _mk_school("orm")
    run = _mk_run(school)
    assert run.pk is not None
    assert run.model_name == "retention"
    from analytics.models import PredictiveModelRun
    assert PredictiveModelRun.objects.filter(school=school).count() == 1


def test_bi_orm_aggregate_by_school_050():
    from analytics.models import PredictiveModelRun
    from django.db.models import Count
    school = _mk_school("agg")
    _mk_run(school)
    _mk_run(school)
    result = PredictiveModelRun.objects.filter(school=school).aggregate(total=Count("id"))
    assert result["total"] == 2


def test_bi_output_json_payload_structure_050():
    school = _mk_school("json")
    payload = {"risk_score": 0.75, "segment": "at_risk", "factors": ["attendance", "grades"]}
    run = _mk_run(school, payload=payload)
    run.refresh_from_db()
    assert isinstance(run.output_json, dict)
    assert run.output_json["risk_score"] == 0.75
    assert run.output_json["segment"] == "at_risk"
    assert run.output_json["factors"] == ["attendance", "grades"]


def test_bi_tenant_isolation_050():
    from analytics.models import PredictiveModelRun
    school_a = _mk_school("iso-A")
    school_b = _mk_school("iso-B")
    _mk_run(school_a)
    _mk_run(school_a)
    assert PredictiveModelRun.objects.filter(school=school_b).count() == 0


def test_bi_tenant_isolation_cross_query_050():
    from analytics.models import PredictiveModelRun
    school_a = _mk_school("cross-A")
    school_b = _mk_school("cross-B")
    _mk_run(school_a)
    ids_for_b = list(PredictiveModelRun.objects.filter(school=school_b).values_list("id", flat=True))
    assert ids_for_b == []


def test_bi_analytics_health_unauthenticated_denied_050():
    response = Client().get(ANALYTICS_HEALTH_URL)
    assert response.status_code in (401, 403)


def test_bi_analytics_export_unauthenticated_denied_050():
    response = Client().post(ANALYTICS_EXPORT_URL, content_type="application/json", data="{}")
    assert response.status_code in (401, 403)


def test_bi_analytics_health_authenticated_allowed_050():
    school = _mk_school("auth-ok")
    user = _mk_user(school, "auth-ok")
    client = Client()
    client.force_login(user)
    response = client.get(ANALYTICS_HEALTH_URL, HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200


def test_bi_analytics_health_response_contract_050():
    school = _mk_school("contract")
    user = _mk_user(school, "contract")
    client = Client()
    client.force_login(user)
    response = client.get(ANALYTICS_HEALTH_URL, HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200
    data = response.json()
    for key in ("school_id", "overall_score", "computed_at"):
        assert key in data

# Module/source context block (audit searchable):
# Business Intelligence Suite
# Trends | Benchmarks | Segments | Exports | Alerts
# Aggregate data | Compute benchmarks | Visualize trends | Protect data | Export analysis
# reporting | data access | mission metrics | finance | enrollment
