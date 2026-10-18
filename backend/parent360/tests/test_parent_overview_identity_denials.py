from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School, UserRole
from households.models import Guardian, Household


pytestmark = pytest.mark.django_db

PARENT360_URL = "/api/parent360/me/overview/"


def test_parent_self_overview_rejects_inactive_linked_account():
    school = School.objects.create(name="Inactive Parent Account School")
    user = get_user_model().objects.create_user(
        username=f"inactive-parent-{school.id}",
        password="test-pass",
        email="inactive-parent@example.com",
        school=school,
        is_active=False,
    )
    UserRole.objects.create(user=user, school=school, role_code="PARENT")
    household = Household.objects.create(
        school_id=school.id,
        name="Inactive Account Family",
        is_active=True,
    )
    Guardian.objects.create(
        school_id=school.id,
        household=household,
        account=user,
        first_name="Pat",
        last_name="Parent",
        email=user.email,
        is_primary=True,
    )

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.get(PARENT360_URL)

    assert response.status_code == 404, response.content
    assert response.json() == {
        "detail": "No active household access is configured for the current account."
    }



def test_dev_heritage_sandbox_parent_continuity_prefers_enrollment_household(settings, monkeypatch):
    from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
    from sandbox_demo.parent_enrollment import seed_parent_enrollment_scenario
    from sandbox_demo.services import seed_heritage_flagship
    from households.models import Guardian, Household
    from applications.models import Application
    from core.models import UserAccount

    settings.DEBUG = False
    settings.ENVIRONMENT = "dev"
    settings.CROWN_ENV = "dev"
    settings.DJANGO_ENV = ""
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    monkeypatch.setenv("CROWN_SANDBOX_ALLOW_OPEN_SESSION", "true")
    monkeypatch.setenv("ENVIRONMENT", "dev")
    monkeypatch.setenv("CROWN_ENV", "dev")
    monkeypatch.setenv("DJANGO_ENV", "")
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    seed_heritage_flagship(reset=True)
    seed_parent_enrollment_scenario()
    parent = UserAccount.objects.get(username=SANDBOX_PERSONAS["parent"].email)
    classroom_household = Household.objects.create(
        school_id=parent.school_id,
        name="Different Classroom Household",
        is_active=True,
    )
    Guardian.objects.create(
        school_id=parent.school_id,
        household=classroom_household,
        account=parent,
        first_name="Demo",
        last_name="Parent",
        email=parent.email,
        is_primary=True,
    )
    application = Application.objects.filter(
        school_id=SANDBOX_SCHOOLS["heritage-core"].id,
        household__name="Reed Family",
    ).latest("created_at")

    client = APIClient()
    client.force_authenticate(user=parent)
    response = client.get("/api/v1/parent360/me/overview/")
    assert response.status_code == 200
    continuity = response.json()["admissions_continuity"]
    assert any(str(app["application_id"]) == str(application.id) for app in continuity["applications"])

    # Production runtime must never activate this DEV-only household override.
    settings.ENVIRONMENT = "production"
    monkeypatch.setenv("ENVIRONMENT", "production")
    from parent360.identity import Parent360IdentityError, resolve_household_for_account
    assert resolve_household_for_account(parent).id != application.household_id
    Guardian.objects.filter(account=parent).delete()
    with pytest.raises(Parent360IdentityError, match="guardian_account_link_required"):
        resolve_household_for_account(parent)
