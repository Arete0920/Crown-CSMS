"""
API permission enforcement tests.

Coverage:
  - /me/entitlements/ requires authenticated user with valid tenant context
  - /plans/ is accessible to authenticated users
  - /ops/<school_id>/ requires an active platform superuser
  - POST /ops/<school_id>/ assigns a new plan and closes the old subscription
"""
import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School
from platform_ops.models import AuditEvent
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

def _make_platform_operator():
    return User.objects.create_superuser(
        username=f"platform_{uuid.uuid4().hex[:8]}",
        email=f"platform_{uuid.uuid4().hex[:8]}@example.invalid",
        password=TEST_AUTH_SECRET,
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
    school_id = School.objects.create(name="Subscription Lookup School").id
    TenantSubscription.objects.create(school_id=school_id, plan=plan)

    operator = _make_platform_operator()
    client = APIClient()
    client.force_authenticate(user=operator)
    resp = client.get(f"/api/v1/subscriptions/ops/{school_id}/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"]["code"] == "smart_start"
    assert str(data["school_id"]) == str(school_id)


def test_ops_get_nonexistent_404():
    operator = _make_platform_operator()
    client = APIClient()
    client.force_authenticate(user=operator)
    resp = client.get(f"/api/v1/subscriptions/ops/{uuid.uuid4()}/")
    assert resp.status_code == 404


def test_ops_post_assigns_plan():
    plan_old = _make_plan("smart_start")
    plan_new = _make_plan("all_access")
    school_id = School.objects.create(name="Subscription Transition School").id
    TenantSubscription.objects.create(school_id=school_id, plan=plan_old)

    operator = _make_platform_operator()
    client = APIClient()
    client.force_authenticate(user=operator)
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
    operator = _make_platform_operator()
    client = APIClient()
    client.force_authenticate(user=operator)
    resp = client.post(
        f"/api/v1/subscriptions/ops/{uuid.uuid4()}/",
        {},
        format="json",
    )
    assert resp.status_code == 400

def test_school_staff_cannot_access_cross_school_subscription_ops():
    plan = _make_plan()
    school_id = uuid.uuid4()
    TenantSubscription.objects.create(school_id=school_id, plan=plan)
    client = APIClient()
    client.force_authenticate(user=_make_staff())
    assert client.get(f"/api/v1/subscriptions/ops/{school_id}/").status_code == 403
    assert client.post(
        f"/api/v1/subscriptions/ops/{school_id}/",
        {"plan_id": plan.pk}, format="json",
    ).status_code == 403
    assert TenantSubscription.objects.filter(
        school_id=school_id, ended_at__isnull=True,
    ).count() == 1


def test_ops_post_rejects_unknown_school_without_orphaned_subscription():
    """An operator cannot assign entitlements to a nonexistent tenant UUID."""
    plan = _make_plan("smart_start")
    missing_id = uuid.uuid4()
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    response = client.post(
        f"/api/v1/subscriptions/ops/{missing_id}/",
        {"plan_id": plan.id, "is_trial": False},
        format="json",
    )
    assert response.status_code == 404
    assert not TenantSubscription.objects.filter(school_id=missing_id).exists()
    assert AuditEvent.objects.count() == 0


@pytest.mark.parametrize(
    "plan_id",
    [True, False, 0, -1, "not-a-plan", "1.5", [], {}, 1.5],
)
def test_ops_post_rejects_invalid_plan_identifiers_without_writing(plan_id):
    school = School.objects.create(name="Invalid Plan Identifier School")
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    response = client.post(
        f"/api/v1/subscriptions/ops/{school.id}/",
        {"plan_id": plan_id},
        format="json",
    )
    assert response.status_code == 400
    assert not TenantSubscription.objects.filter(school_id=school.id).exists()
    assert AuditEvent.objects.count() == 0


@pytest.mark.parametrize("is_trial", ["false", "true", 0, 1, None, {}])
def test_ops_post_requires_explicit_json_boolean(is_trial):
    school = School.objects.create(name="Trial Boolean School")
    plan = _make_plan("smart_start")
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    response = client.post(
        f"/api/v1/subscriptions/ops/{school.id}/",
        {"plan_id": plan.id, "is_trial": is_trial},
        format="json",
    )
    assert response.status_code == 400
    assert not TenantSubscription.objects.filter(school_id=school.id).exists()
    assert AuditEvent.objects.count() == 0


def test_ops_post_rejects_inactive_plan_without_mutating_history():
    school = School.objects.create(name="Inactive Plan School")
    old = _make_plan("smart_start")
    retired = _make_plan("retired")
    retired.is_active = False
    retired.save(update_fields=["is_active"])
    original = TenantSubscription.objects.create(school_id=school.id, plan=old)
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    response = client.post(
        f"/api/v1/subscriptions/ops/{school.id}/",
        {"plan_id": retired.id, "is_trial": False},
        format="json",
    )
    assert response.status_code == 404
    original.refresh_from_db()
    assert original.ended_at is None
    assert TenantSubscription.objects.filter(school_id=school.id).count() == 1
    assert AuditEvent.objects.count() == 0


def test_ops_post_same_subscription_is_idempotent_without_new_audit():
    school = School.objects.create(name="Idempotent Subscription School")
    plan = _make_plan("smart_start")
    previous = TenantSubscription.objects.create(
        school_id=school.id, plan=plan, is_trial=True
    )
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    url = f"/api/v1/subscriptions/ops/{school.id}/"
    for _ in range(2):
        response = client.post(
            url, {"plan_id": plan.id, "is_trial": True}, format="json"
        )
        assert response.status_code == 200
        assert response.json()["id"] == previous.id
    assert TenantSubscription.objects.filter(school_id=school.id).count() == 1
    assert AuditEvent.objects.count() == 0


def test_ops_post_change_is_history_preserving_and_audited():
    school = School.objects.create(name="Audited Subscription School")
    old_plan = _make_plan("smart_start")
    new_plan = _make_plan("next_level")
    previous = TenantSubscription.objects.create(
        school_id=school.id, plan=old_plan, is_trial=False
    )
    operator = _make_platform_operator()
    client = APIClient()
    client.force_authenticate(user=operator)
    response = client.post(
        f"/api/v1/subscriptions/ops/{school.id}/",
        {"plan_id": new_plan.id, "is_trial": True},
        format="json",
    )
    assert response.status_code == 201
    previous.refresh_from_db()
    assert previous.ended_at is not None
    new = TenantSubscription.objects.get(
        school_id=school.id, ended_at__isnull=True
    )
    assert new.plan == new_plan
    assert new.is_trial is True
    assert new.started_at == previous.ended_at
    assert TenantSubscription.objects.filter(school_id=school.id).count() == 2
    event = AuditEvent.objects.get(action="subscription.plan_changed")
    assert event.school_id == school.id
    assert event.actor_user_id == operator.id
    assert event.resource_kind == "School"
    assert event.payload == {
        "previous_plan": "smart_start",
        "new_plan": "next_level",
        "previous_trial": False,
        "new_trial": True,
    }


def test_ops_post_initial_assignment_requires_existing_school_and_is_audited():
    school = School.objects.create(name="First Subscription School")
    plan = _make_plan("smart_start")
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    response = client.post(
        f"/api/v1/subscriptions/ops/{school.id}/",
        {"plan_id": plan.id},
        format="json",
    )
    assert response.status_code == 201
    assert TenantSubscription.objects.filter(
        school_id=school.id, ended_at__isnull=True
    ).count() == 1
    assert AuditEvent.objects.filter(
        school_id=school.id,
        action="subscription.plan_assigned",
    ).count() == 1


def test_ops_get_and_post_reject_ambiguous_active_subscription_history():
    """Preexisting corrupt state requires reconciliation, not guessing."""
    school = School.objects.create(name="Ambiguous Subscription School")
    old = _make_plan("smart_start")
    other = _make_plan("next_level")
    TenantSubscription.objects.create(school_id=school.id, plan=old)
    TenantSubscription.objects.create(school_id=school.id, plan=other)
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    url = f"/api/v1/subscriptions/ops/{school.id}/"
    assert client.get(url).status_code == 409
    assert client.post(
        url, {"plan_id": other.id, "is_trial": False}, format="json"
    ).status_code == 409
    assert TenantSubscription.objects.filter(
        school_id=school.id, ended_at__isnull=True
    ).count() == 2
    assert AuditEvent.objects.count() == 0


def test_ops_post_audit_failure_rolls_back_subscription_changes():
    school = School.objects.create(name="Audit Rollback School")
    old = _make_plan("smart_start")
    new = _make_plan("all_access")
    previous = TenantSubscription.objects.create(school_id=school.id, plan=old)
    client = APIClient()
    client.force_authenticate(user=_make_platform_operator())
    client.raise_request_exception = False
    with patch(
        "subscriptions.api.views.AuditEvent.objects.create",
        side_effect=RuntimeError("Simulated audit storage failure"),
    ):
        response = client.post(
            f"/api/v1/subscriptions/ops/{school.id}/",
            {"plan_id": new.id, "is_trial": False},
            format="json",
        )
    assert response.status_code == 500
    previous.refresh_from_db()
    assert previous.ended_at is None
    assert TenantSubscription.objects.filter(
        school_id=school.id, ended_at__isnull=True
    ).count() == 1
    assert AuditEvent.objects.count() == 0
