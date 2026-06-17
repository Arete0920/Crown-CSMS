import uuid

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client

from core.models import School
from households.models import Household


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
