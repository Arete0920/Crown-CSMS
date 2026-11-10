"""Invite scopes must never expand explicit invalid operator input."""

from datetime import timedelta
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from sandbox_demo.catalog import DEFAULT_SANDBOX_INVITE_ROLES
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
    assert kwargs["allowed_roles"] == list(DEFAULT_SANDBOX_INVITE_ROLES)
    assert kwargs["allowed_seed_packs"] == ["heritage-core"]
    assert kwargs["track"] == "school"


def test_hosted_daycare_roles_require_explicit_operator_scope(invite_store):
    """A new role never appears in omitted defaults; a named grant is preserved."""
    assert "daycare_director" not in DEFAULT_SANDBOX_INVITE_ROLES
    assert "daycare_staff" not in DEFAULT_SANDBOX_INVITE_ROLES
    response = create_invite({
        "allowed_roles": ["daycare_director"],
        "allowed_seed_packs": ["heritage-core"],
    })
    assert response.status_code == 201
    assert invite_store.call_args.kwargs["allowed_roles"] == ["daycare_director"]


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


@pytest.mark.django_db
def test_cli_omitted_roles_do_not_expand_hosted_childcare_authority():
    """Both operator entry points retain least privilege after catalog expansion."""
    call_command(
        "sandbox_create_invite",
        organization="Fictional CLI default",
        base_url="https://example.invalid",
        stdout=StringIO(),
    )
    invite = SandboxInvite.objects.get(organization_label="Fictional CLI default")
    assert invite.allowed_roles == DEFAULT_SANDBOX_INVITE_ROLES
    assert "daycare_director" not in invite.allowed_roles
    assert "daycare_staff" not in invite.allowed_roles


@pytest.mark.django_db
def test_cli_explicit_childcare_grant_is_preserved_but_unknown_role_is_blocked():
    call_command(
        "sandbox_create_invite",
        organization="Fictional explicit daycare",
        base_url="https://example.invalid",
        roles="daycare_director",
        stdout=StringIO(),
    )
    invite = SandboxInvite.objects.get(organization_label="Fictional explicit daycare")
    assert invite.allowed_roles == ["daycare_director"]
    before = SandboxInvite.objects.count()
    with pytest.raises(CommandError, match="Invalid sandbox invite scope"):
        call_command(
            "sandbox_create_invite",
            organization="Unknown privileged grant",
            base_url="https://example.invalid",
            roles="daycare_director,unknown_privileged_role",
            stdout=StringIO(),
        )
    assert SandboxInvite.objects.count() == before


@pytest.mark.django_db
def test_school_staff_cannot_administer_buyer_invitations(settings):
    """Django staff and school-bound superusers are not global operators."""
    from core.models import School, UserAccount

    settings.CROWN_OPS_SECRET = ""
    settings.DEV_OPS_SECRET = ""
    school = School.objects.create(name="Synthetic invite authority school")
    staff = UserAccount.objects.create_user(
        username="synthetic-invite-staff",
        email="invite-staff@example.test",
        school=school, is_staff=True,
    )
    bound_superuser = UserAccount.objects.create_user(
        username="synthetic-invite-bound-superuser",
        email="invite-bound-superuser@example.test",
        school=school, is_staff=True, is_superuser=True,
    )
    invite = SandboxInvite.objects.create(
        organization_label="Synthetic buyer invitation",
        track="school",
        allowed_roles=["teacher"],
        allowed_seed_packs=["heritage-core"],
        expires_at=timezone.now() + timedelta(days=7),
    )
    initial_count = SandboxInvite.objects.count()

    for actor in (staff, bound_superuser):
        client = APIClient()
        client.force_authenticate(user=actor)
        create = client.post(
            reverse("sandbox-invite-create"), {"days": 7}, format="json",
        )
        assert create.status_code == 403
        assert create.json()["code"] == "sandbox_ops_required"
        revoke = client.post(
            reverse("sandbox-invite-revoke", kwargs={"invite_id": invite.pk}),
            {}, format="json",
        )
        assert revoke.status_code == 403
        assert revoke.json()["code"] == "sandbox_ops_required"
        assert SandboxInvite.objects.count() == initial_count
        invite.refresh_from_db()
        assert invite.revoked_at is None


@pytest.mark.django_db
def test_active_schoolless_platform_operator_can_administer_buyer_invitations(settings):
    """An active schoolless superuser retains the established platform pathway."""
    from core.models import UserAccount

    settings.CROWN_OPS_SECRET = ""
    settings.DEV_OPS_SECRET = ""
    owner = UserAccount.objects.create_superuser(
        username="synthetic-invite-platform-owner",
        email="invite-platform-owner@example.test",
        password="synthetic-not-used",
    )
    client = APIClient()
    client.force_authenticate(user=owner)
    created = client.post(
        reverse("sandbox-invite-create"),
        {"days": 7, "allowed_roles": ["teacher"],
         "allowed_seed_packs": ["heritage-core"]},
        format="json",
    )
    assert created.status_code == 201, created.data
    invite_id = created.data["invite_id"]
    assert SandboxInvite.objects.get(pk=invite_id).revoked_at is None
    revoked = client.post(
        reverse("sandbox-invite-revoke", kwargs={"invite_id": invite_id}),
        {}, format="json",
    )
    assert revoked.status_code == 200, revoked.data
    assert SandboxInvite.objects.get(pk=invite_id).revoked_at is not None

    owner.is_active = False
    owner.save(update_fields=["is_active"])
    denied = client.post(
        reverse("sandbox-invite-create"), {"days": 7}, format="json",
    )
    assert denied.status_code in (401, 403)
