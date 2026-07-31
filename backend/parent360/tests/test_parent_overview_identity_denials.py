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
