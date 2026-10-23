"""Invite scopes must never expand explicit invalid operator input."""

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from sandbox_demo.catalog import SANDBOX_PERSONAS
from sandbox_demo.models import SandboxInvite


@pytest.fixture
def invite_store(settings, monkeypatch):
    """Observe the write boundary without storing any invitation or credential."""
    settings.CROWN_OPS_SECRET = "test-invite-ops-secret"
    create = Mock(
        return_value=SimpleNamespace(
            id="sbx_inv_test_scope",
            expires_at=timezone.now() + timedelta(days=7),
        )
    )
    monkeypatch.setattr(
        "sandbox_demo.views.SandboxInvite",
        SimpleNamespace(objects=SimpleNamespace(create=create)),
    )
    return create


def create_invite(payload):
    """Use the real API route and operator-secret authorization boundary."""
    return APIClient().post(
        reverse("sandbox-invite-create"),
        {"days": 7, **payload},
        format="json",
        HTTP_X_CROWN_OPS_SECRET="test-invite-ops-secret",
    )


@pytest.mark.parametrize("field", ("allowed_roles", "allowed_seed_packs"))
@pytest.mark.parametrize(
    "value", (None, "", False, 0, [], {}, "teacher", [None], [{}], ["unknown"])
)
def test_invalid_scope_never_creates_invitation(invite_store, field, value):
    """Empty, malformed and unknown scopes cannot grant broader access."""
    response = create_invite({field: value})

    assert response.status_code == 400
    assert response.json()["code"] == f"sandbox_invite_{field}_invalid"
    invite_store.assert_not_called()


@pytest.mark.parametrize("value", (None, "", False, 0, [], {}, "unknown"))
def test_invalid_track_never_creates_invitation(invite_store, value):
    """Invites must name the supported school track."""
    response = create_invite({"track": value})

    assert response.status_code == 400
    assert response.json()["code"] == "sandbox_invite_track_invalid"
    invite_store.assert_not_called()


def test_omitted_scope_preserves_operator_defaults(invite_store):
    """Only omitted fields choose the documented default access scope."""
    response = create_invite({})

    assert response.status_code == 201
    kwargs = invite_store.call_args.kwargs
    assert kwargs["allowed_roles"] == list(SANDBOX_PERSONAS)
    assert kwargs["allowed_seed_packs"] == ["heritage-core"]
    assert kwargs["track"] == "school"


def test_explicit_restricted_scope_is_preserved(invite_store):
    """A teacher-only invitation remains teacher-only at the write boundary."""
    response = create_invite(
        {"allowed_roles": ["teacher"], "allowed_seed_packs": ["heritage-core"]}
    )

    assert response.status_code == 201
    kwargs = invite_store.call_args.kwargs
    assert kwargs["allowed_roles"] == ["teacher"]
    assert kwargs["allowed_seed_packs"] == ["heritage-core"]


def test_unauthorized_request_cannot_create_invitation(invite_store):
    """Scope handling must retain operator authorization before any write."""
    response = APIClient().post(
        reverse("sandbox-invite-create"), {"days": 7}, format="json"
    )

    assert response.status_code == 403
    assert response.json()["code"] == "sandbox_ops_required"
    invite_store.assert_not_called()


@pytest.mark.django_db
def test_restricted_invite_persists_and_enforces_its_role(settings):
    """A stored teacher-only invite denies admin access and permits teaching."""
    settings.CROWN_OPS_SECRET = "test-invite-ops-secret"
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = False
    response = create_invite(
        {"allowed_roles": ["teacher"], "allowed_seed_packs": ["heritage-core"]}
    )
    assert response.status_code == 201
    invite = SandboxInvite.objects.get(pk=response.json()["invite_id"])
    assert invite.allowed_roles == ["teacher"]
    assert invite.allowed_seed_packs == ["heritage-core"]

    client = APIClient()
    payload = {"invite_id": invite.id, "school": "heritage-core", "track": "school"}
    denied = client.post(
        reverse("sandbox-session"),
        {**payload, "role": "school_admin"},
        format="json",
    )
    assert denied.status_code == 403
    assert denied.json()["code"] == "sandbox_invite_role_not_allowed"
    invite.refresh_from_db()
    assert invite.last_used_at is None
    assert "_auth_user_id" not in client.session

    allowed = client.post(
        reverse("sandbox-session"), {**payload, "role": "teacher"}, format="json"
    )
    assert allowed.status_code == 201
    assert allowed.json()["role"] == "teacher"
    invite.refresh_from_db()
    assert invite.last_used_at is not None
