from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from core.models import School
from households.models import Guardian, Household
from parent360.identity import Parent360IdentityError, resolve_household_for_account


pytestmark = pytest.mark.django_db


def _make_user(school: School, *, email: str = "parent@example.com"):
    return get_user_model().objects.create_user(
        username=f"parent-{school.id}",
        password="test-pass",
        email=email,
        school=school,
    )


def _make_household(school: School, *, active: bool = True) -> Household:
    return Household.objects.create(
        school_id=school.id,
        name=f"{school.name} Household",
        is_active=active,
    )


def _make_guardian(
    school: School,
    household: Household,
    *,
    account=None,
    email: str = "parent@example.com",
) -> Guardian:
    return Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=account,
        first_name="Pat",
        last_name="Parent",
        email=email,
        is_primary=True,
    )


def test_resolver_returns_household_for_explicit_same_school_account_link():
    school = School.objects.create(name="Canonical Parent School")
    user = _make_user(school)
    household = _make_household(school)
    _make_guardian(school, household, account=user)

    assert resolve_household_for_account(user) == household


def test_resolver_does_not_fall_back_to_matching_email():
    school = School.objects.create(name="No Email Authorization School")
    user = _make_user(school, email="shared@example.com")
    household = _make_household(school)
    _make_guardian(school, household, email="shared@example.com")

    with pytest.raises(Parent360IdentityError, match="guardian_account_link_required"):
        resolve_household_for_account(user)


def test_guardian_rejects_account_from_another_school():
    school = School.objects.create(name="Guardian School")
    other_school = School.objects.create(name="Foreign Account School")
    user = _make_user(other_school)
    household = _make_household(school)

    guardian = Guardian(
        school_id=school.id,
        household=household,
        account=user,
        first_name="Pat",
        last_name="Parent",
    )

    with pytest.raises(ValidationError, match="same school"):
        guardian.save()


def test_resolver_rejects_inactive_account():
    school = School.objects.create(name="Inactive Account School")
    user = _make_user(school)
    user.is_active = False
    user.save(update_fields=["is_active"])
    household = _make_household(school)
    _make_guardian(school, household, account=user)

    with pytest.raises(Parent360IdentityError, match="inactive_account"):
        resolve_household_for_account(user)


def test_resolver_rejects_inactive_household():
    school = School.objects.create(name="Inactive Household School")
    user = _make_user(school)
    household = _make_household(school, active=False)
    _make_guardian(school, household, account=user)

    with pytest.raises(Parent360IdentityError, match="inactive_household"):
        resolve_household_for_account(user)
