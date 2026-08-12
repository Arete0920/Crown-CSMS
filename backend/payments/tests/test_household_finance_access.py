import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from core.models import School
from households.models import Household
from payments.models import StatementExportRequest


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school, *, is_staff=False, role_groups=()):
    User = get_user_model()
    user = User.objects.create_user(
        username=f"user-{uuid.uuid4()}",
        password="pass12345!",
        is_staff=is_staff,
    )
    if hasattr(user, "school_id"):
        setattr(user, "school_id", school.id)
        user.save(update_fields=["school_id"])

    for group_name in role_groups:
        group, _ = Group.objects.get_or_create(name=group_name)
        user.groups.add(group)

    return user


def test_household_summary_allows_finance_runtime_role():
    school = School.objects.create(name="Payment Provider School")
    household = Household.objects.create(school_id=school.id, name="Family One")
    user = _mk_user_with_school(
        school,
        is_staff=True,
        role_groups=("finance_admin",),
    )

    client = Client()
    client.force_login(user)

    resp = client.get(
        f"/api/v1/payments/accounts/{household.id}/summary/",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert resp.status_code == 200
    payload = resp.json()
    assert payload["household_id"] == str(household.id)
    assert "summary" in payload


def test_household_summary_blocks_non_finance_non_household_user():
    school = School.objects.create(name="Payment Provider School")
    household = Household.objects.create(school_id=school.id, name="Family One")
    user = _mk_user_with_school(
        school,
        is_staff=False,
        role_groups=("parent",),
    )

    client = Client()
    client.force_login(user)

    resp = client.get(
        f"/api/v1/payments/accounts/{household.id}/summary/",
        **{"HTTP_X_SCHOOL_ID": str(school.id)},
    )

    assert resp.status_code == 403


def test_finance_role_cannot_cross_school_household_boundary():
    school_a = School.objects.create(name="Finance Boundary School A")
    school_b = School.objects.create(name="Finance Boundary School B")
    foreign_household = Household.objects.create(school_id=school_b.id, name="Foreign Family")
    user = _mk_user_with_school(
        school_a,
        is_staff=True,
        role_groups=("finance_admin",),
    )

    client = Client()
    client.force_login(user)
    headers = {"HTTP_X_SCHOOL_ID": str(school_a.id)}

    endpoints = [
        f"/api/v1/payments/accounts/{foreign_household.id}/summary/",
        f"/api/v1/payments/accounts/{foreign_household.id}/history/",
        f"/api/v1/payments/accounts/{foreign_household.id}/statement.csv",
        f"/api/v1/payments/accounts/{foreign_household.id}/methods/",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint, **headers)
        assert response.status_code == 403, endpoint

    setup_response = client.post(
        f"/api/v1/payments/accounts/{foreign_household.id}/methods/setup/",
        data={},
        content_type="application/json",
        **headers,
    )
    assert setup_response.status_code == 403
    assert not StatementExportRequest.objects.filter(
        school_id=school_a.id,
        household_id=foreign_household.id,
    ).exists()
