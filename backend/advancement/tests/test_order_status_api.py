from __future__ import annotations

import uuid

import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from advancement.api import order_status
from advancement.models_stage3_2 import PendingSeatOrder
from core.models import CrownPermission, RolePermission, School, UserRole


@pytest.fixture
def school_user(django_user_model):
    school = School.objects.create(name=f"Order Status {uuid.uuid4().hex[:8]}")
    user = django_user_model.objects.create_user(
        username=f"order_status_{uuid.uuid4().hex[:8]}",
        password="pass",
        school=school,
    )
    UserRole.objects.create(school=school, user=user, role_code="HEAD_OF_SCHOOL")
    permission, _ = CrownPermission.objects.get_or_create(
        code="advancement.view",
        defaults={"description": "Advancement view"},
    )
    RolePermission.objects.get_or_create(role_code="HEAD_OF_SCHOOL", permission=permission)
    return school, user


def _request_for(user, school):
    request = APIRequestFactory().get("/orders/status/")
    request.school = school
    force_authenticate(request, user=user)
    return request


@pytest.mark.django_db
def test_order_status_returns_same_tenant_order(school_user):
    school, user = school_user
    order = PendingSeatOrder.objects.create(
        school_id=school.id,
        event_id=uuid.uuid4(),
        purchaser_name="Buyer",
        purchaser_email="buyer@example.com",
        seat_ids=[str(uuid.uuid4())],
        amount_cents=2500,
        status="pending",
    )

    response = order_status(_request_for(user, school), order.id)

    assert response.status_code == 200
    assert response.data["order_id"] == str(order.id)
    assert response.data["status"] == "pending"


@pytest.mark.django_db
def test_order_status_does_not_cross_tenant_boundary(school_user):
    school, user = school_user
    other_school = School.objects.create(name=f"Other {uuid.uuid4().hex[:8]}")
    order = PendingSeatOrder.objects.create(
        school_id=other_school.id,
        event_id=uuid.uuid4(),
        purchaser_name="Other Buyer",
        purchaser_email="other@example.com",
        seat_ids=[str(uuid.uuid4())],
        amount_cents=2500,
        status="pending",
    )

    response = order_status(_request_for(user, school), order.id)

    assert response.status_code == 404
