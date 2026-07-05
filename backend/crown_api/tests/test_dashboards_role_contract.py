"""
Dashboard Role API contract tests — Me / Summary / Drilldown / Alerts.

Contract invariants:
  1. Missing X-School-Id header → 401 (unauthenticated) or 400 (missing header)
  2. Invalid UUID header → 400
  3. Nonexistent school → 404
  4. Valid tenant + authenticated → 200 with correct schema
  5. Summary widget list is non-empty and sorted by priority
  6. Each widget has stable type, key, size, priority, data fields
"""
import pytest
from django.contrib.auth import get_user_model

from rest_framework.test import APIClient
from core.models import School

User = get_user_model()

ENDPOINTS = [
    "/api/dashboards/me/",
    "/api/dashboards/summary/",
    "/api/dashboards/drilldown/?widget=alerts_flip",
    "/api/dashboards/alerts/",
]


@pytest.fixture()
def school(db):
    return School.objects.create(name="Contract Test School")


@pytest.fixture()
def user(db, school):
    return User.objects.create_user(
        username="dash_test_user",
        email="dash@test.com",
        password="pw",
        school_id=school.id,
    )


@pytest.fixture()
def auth_client(db, user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


@pytest.fixture()
def anon_client():
    return APIClient()


# ---------------------------------------------------------------------------
# Authentication gate
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_unauthenticated_returns_401(anon_client, school, endpoint):
    """All endpoints require authentication.

    DRF returns 403 (not 401) when SessionAuthentication is used and no
    credentials are provided — both mean "not allowed without auth".
    """
    resp = anon_client.get(endpoint, HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code in (401, 403), (
        f"{endpoint} should 401 or 403 for anon (got {resp.status_code})"
    )


# ---------------------------------------------------------------------------
# Tenant header required
# ---------------------------------------------------------------------------

@pytest.mark.django_db
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_missing_school_header_returns_400(auth_client, endpoint):
    """Missing X-School-Id → 400."""
    resp = auth_client.get(endpoint)
    assert resp.status_code == 400, f"{endpoint} should 400 when header missing"


@pytest.mark.django_db
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_invalid_school_uuid_returns_400(auth_client, endpoint):
    """Non-UUID school_id → 400."""
    resp = auth_client.get(endpoint, HTTP_X_SCHOOL_ID="not-a-uuid")
    assert resp.status_code == 400, f"{endpoint} should 400 on bad UUID"


@pytest.mark.django_db
@pytest.mark.parametrize("endpoint", ENDPOINTS)
def test_nonexistent_school_returns_404(auth_client, endpoint):
    """Valid UUID but school doesn't exist → 404."""
    resp = auth_client.get(endpoint, HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404, f"{endpoint} should 404 for missing school"


# ---------------------------------------------------------------------------
# 200 happy-path: schema checks
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_dashboard_me_returns_schema(auth_client, school, user):
    resp = auth_client.get("/api/dashboards/me/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200, resp.data
    data = resp.json()
    assert "school_id" in data
    assert "roles" in data
    assert isinstance(data["roles"], list)
    assert len(data["roles"]) >= 1
    assert "default_route" in data
    assert "features" in data


@pytest.mark.django_db
def test_dashboard_summary_returns_widgets(auth_client, school):
    resp = auth_client.get("/api/dashboards/summary/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200, resp.data
    data = resp.json()
    assert data["school_id"] == str(school.id)
    assert "widgets" in data
    widgets = data["widgets"]
    assert isinstance(widgets, list)
    assert len(widgets) >= 1, "Summary must return at least one widget"


@pytest.mark.django_db
def test_dashboard_summary_widgets_sorted_by_priority(auth_client, school):
    resp = auth_client.get("/api/dashboards/summary/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    widgets = resp.json()["widgets"]
    priorities = [w["priority"] for w in widgets]
    assert priorities == sorted(priorities), "Widgets must be sorted by priority ascending"


@pytest.mark.django_db
def test_dashboard_summary_widget_schema(auth_client, school):
    """Every widget has all required fields."""
    resp = auth_client.get("/api/dashboards/summary/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    for w in resp.json()["widgets"]:
        assert "key" in w, f"Missing 'key' on widget {w}"
        assert "type" in w, f"Missing 'type' on widget {w}"
        assert "title" in w, f"Missing 'title' on widget {w}"
        assert "size" in w, f"Missing 'size' on widget {w}"
        assert w["size"] in ("sm", "md", "lg"), f"Bad size on widget {w}"
        assert "priority" in w, f"Missing 'priority' on widget {w}"
        assert "data" in w, f"Missing 'data' on widget {w}"


@pytest.mark.django_db
def test_dashboard_summary_quick_actions_always_present(auth_client, school):
    """quick_actions widget is present for all roles."""
    resp = auth_client.get("/api/dashboards/summary/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    keys = [w["key"] for w in resp.json()["widgets"]]
    assert "quick_actions" in keys, "quick_actions widget must always be present"


@pytest.mark.django_db
def test_dashboard_drilldown_requires_widget_param(auth_client, school):
    """drilldown without ?widget= → 400."""
    resp = auth_client.get("/api/dashboards/drilldown/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 400


@pytest.mark.django_db
def test_dashboard_drilldown_returns_schema(auth_client, school):
    resp = auth_client.get(
        "/api/dashboards/drilldown/?widget=alerts_flip",
        HTTP_X_SCHOOL_ID=str(school.id),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["widget"] == "alerts_flip"
    assert data["school_id"] == str(school.id)
    assert "rows" in data
    assert "page" in data


@pytest.mark.django_db
def test_dashboard_alerts_returns_list(auth_client, school):
    resp = auth_client.get("/api/dashboards/alerts/", HTTP_X_SCHOOL_ID=str(school.id))
    assert resp.status_code == 200
    data = resp.json()
    assert "alerts" in data
    assert isinstance(data["alerts"], list)
    for alert in data["alerts"]:
        assert "key" in alert
        assert "level" in alert
        assert alert["level"] in ("good", "warn", "bad", "info")
        assert "text" in alert


# ---------------------------------------------------------------------------
# Cross-tenant: user from school A cannot access school B's data
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_cross_tenant_access_blocked(db):
    school_a = School.objects.create(name="Tenant A")
    school_b = School.objects.create(name="Tenant B")
    user_a = User.objects.create_user(
        username="tenant_a_user", email="a@test.com", password="pw",
        school_id=school_a.id,
    )
    c = APIClient()
    c.force_authenticate(user=user_a)
    resp = c.get("/api/dashboards/summary/", HTTP_X_SCHOOL_ID=str(school_b.id))
    assert resp.status_code in (403, 404), (
        f"User from school A accessing school B data should be blocked (got {resp.status_code})"
    )
