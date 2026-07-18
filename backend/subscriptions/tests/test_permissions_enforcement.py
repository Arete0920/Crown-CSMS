"""
API permission enforcement tests.

Coverage:
  - /me/entitlements/ requires authenticated user with valid tenant context
  - /plans/ is accessible to authenticated users
  - /ops/<school_id>/ requires staff/admin
  - POST /ops/<school_id>/ assigns a new plan and closes the old subscription
"""
import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School
from subscriptions.models import Plan, TenantSubscription

pytestmark = pytest.mark.django_db

User = get_user_model()
TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"


def _make_plan(code="smart_start"):
    plan, _ = Plan.objects.get_or_create(
        code=code, defaults={"name": code.replace("_", " ").title(), "sort_order": 10}
    )
    return plan


def _make_staff():
    return User.objects.create_user(
        username=f"staff_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        is_staff=True,
    )


def _make_user(*, school=None):
    return User.objects.create_user(
        username=f"user_{uuid.uuid4().hex[:8]}",
        password=TEST_AUTH_SECRET,
        school=school,
    )


def test_me_entitlements_requires_auth():
    resp = APIClient().get("/api/v1/subscriptions/me/entitlements/")
    assert resp.status_code in (401, 403)


def test_me_entitlements_requires_tenant_context():
    user = _make_user()
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/v1/subscriptions/me/entitlements/")
    assert resp.status_code == 400
    assert resp.json()["error"] == "X-School-ID header is required."


def test_me_entitlements_returns_snapshot_for_matching_canonical_tenant():
    plan = _make_plan()
    school = School.objects.create(name="Entitlement Academy")
    TenantSubscription.objects.create(school_id=school.id, plan=plan)

    user = _make_user(school=school)
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(
        "/api/v1/subscriptions/me/entitlements/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["plan_code"] == "smart_start"
    assert payload["plan_name"] == plan.name
    assert payload["is_trial"] is False
    assert isinstance(payload["entitlements"], dict)


def test_plan_list_authenticated():
    _make_plan("smart_start")
    user = _make_user()
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get("/api/v1/subscriptions/plans/")
    assert resp.status_code == 200
    codes = [p["code"] for p in resp.json()]
    assert "smart_start" in codes


def test_plan_list_requires_auth():
    resp = APIClient().get("/api/v1/subscriptions/plans/")
    assert resp.status_code in (401, 403)


def test_ops_requires_admin():
    plan = _make_plan()
    school_id = uuid.uuid4()
    TenantSubscription.objects.create(school_id=school_id, plan=plan)

    user = _make_user()
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.get(f"/api/v1/subscriptions/ops/{school_id}/")
    assert resp.status_code == 403


def test_ops_get_subscription():
    plan = _make_plan()
    school_id = uuid.uuid4()
    TenantSubscription.objects.create(school_id=school_id, plan=plan)

    staff = _make_staff()
    client = APIClient()
    client.force_authenticate(user=staff)
    resp = client.get(f"/api/v1/subscriptions/ops/{school_id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"]["code"] == "smart_start"
    assert str(data["school_id"]) == str(school_id)


def test_ops_get_nonexistent_404():
    staff = _make_staff()
    client = APIClient()
    client.force_authenticate(user=staff)
    resp = client.get(f"/api/v1/subscriptions/ops/{uuid.uuid4()}/")
    assert resp.status_code == 404


def test_ops_post_assigns_plan():
    plan_old = _make_plan("smart_start")
    plan_new = _make_plan("all_access")
    school_id = uuid.uuid4()
    TenantSubscription.objects.create(school_id=school_id, plan=plan_old)

    staff = _make_staff()
    client = APIClient()
    client.force_authenticate(user=staff)
    resp = client.post(
        f"/api/v1/subscriptions/ops/{school_id}/",
        {"plan_id": plan_new.pk, "is_trial": False},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.json()["plan"]["code"] == "all_access"

    old_sub = TenantSubscription.objects.get(school_id=school_id, plan=plan_old)
    assert old_sub.ended_at is not None


def test_ops_post_missing_plan_id():
    staff = _make_staff()
    client = APIClient()
    client.force_authenticate(user=staff)
    resp = client.post(
        f"/api/v1/subscriptions/ops/{uuid.uuid4()}/",
        {},
        format="json",
    )
    assert resp.status_code == 400
