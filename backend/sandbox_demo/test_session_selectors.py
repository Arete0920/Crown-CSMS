"""Session selectors must resolve explicitly before authentication or writes."""

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount
from sandbox_demo.catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from sandbox_demo.models import SandboxEvent


@pytest.mark.django_db
@pytest.mark.parametrize("field", ("role", "school", "track"))
@pytest.mark.parametrize(
    "value", (None, "", False, 0, [], {}, ["teacher"], {"key": "heritage"}, "unknown")
)
def test_invalid_selector_rejected_before_writes(settings, field, value):
    """Explicit invalid values cannot silently select a privileged default."""
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True
    payload = {"role": "teacher", "school": "heritage", "track": "school"}
    payload[field] = value
    models = (School, UserAccount, CrownPermission, RolePermission, SandboxEvent)
    before = tuple(model.objects.count() for model in models)
    client = APIClient()

    response = client.post(reverse("sandbox-session"), payload, format="json")

    assert response.status_code == 400
    assert response.json()["code"] == f"sandbox_{field}_invalid"
    assert tuple(model.objects.count() for model in models) == before
    assert "_auth_user_id" not in client.session


@pytest.mark.django_db
@pytest.mark.parametrize("role", tuple(SANDBOX_PERSONAS))
def test_known_persona_can_create_session(settings, role):
    """Validation preserves every supported persona and the Heritage alias."""
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True

    response = APIClient().post(
        reverse("sandbox-session"),
        {"role": role, "school": "heritage", "track": "school"},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["role"] == role
    assert response.json()["school_id"] == SANDBOX_SCHOOLS["heritage-core"].id


@pytest.mark.django_db
def test_omitted_selectors_keep_documented_defaults(settings):
    """An omitted selector retains compatibility with the default session."""
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = True

    response = APIClient().post(reverse("sandbox-session"), {}, format="json")

    assert response.status_code == 201
    assert response.json()["role"] == "school_admin"
    assert response.json()["school_id"] == SANDBOX_SCHOOLS["heritage-core"].id
