"""Normal password/JWT access, never a synthetic token or schoolless login."""
import secrets

import pytest
from django.core.management.base import CommandError
from rest_framework.test import APIClient

from core.models import School, UserAccount, UserRole
from sandbox_demo.catalog import SANDBOX_PERSONAS
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_access import initialize_presenter_passwords
from sandbox_demo.universal_demo import prepare_presenter
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID, presenter_username

pytestmark = pytest.mark.django_db


@pytest.fixture
def operator_secrets(monkeypatch):
    class PrivateSecrets(dict):
        def __repr__(self):
            return "<private synthetic test secrets>"
    values = PrivateSecrets({key: secrets.token_urlsafe(32) for key in SANDBOX_PERSONAS})
    for key, value in values.items():
        monkeypatch.setenv(f"CROWN_PRESENTER_{key.upper()}_PASSWORD", value)
    return values


def login(key, passwords):
    client = APIClient()
    response = client.post("/api/v1/auth/token/", {
        "username": presenter_username(key), "password": passwords[key],
    }, format="json")
    assert response.status_code == 200, response.content
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}",
                       HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID))
    return client, response.json()


def test_all_presenter_personas_use_existing_login_and_scoped_role_context(local_runtime, operator_secrets, capsys):
    prepare_presenter(apply=True, enable_password_login=True)
    for key, persona in SANDBOX_PERSONAS.items():
        client, tokens = login(key, operator_secrets)
        assert tokens.get("refresh")
        identity = client.get("/api/system/whoami/")
        assert identity.status_code == 200, identity.content
        assert identity.json()["user"]["school_id"] == str(UNIVERSAL_SCHOOL_ID)
        context = client.get("/api/v1/dashboards/me/")
        assert context.status_code == 200, context.content
        assert persona.role_code.lower() in [role.lower() for role in context.json()["roles"]]
    assert all(secret not in capsys.readouterr().out for secret in operator_secrets.values())
    assert not UserAccount.objects.filter(is_staff=True).exists()
    assert not UserAccount.objects.filter(is_superuser=True).exists()


def test_initialization_does_not_rotate_existing_credentials(local_runtime, operator_secrets):
    prepare_presenter(apply=True, enable_password_login=True)
    before = dict(UserAccount.objects.values_list("pk", "password"))
    with pytest.raises(CommandError, match="already exists"):
        prepare_presenter(apply=True, enable_password_login=True)
    with pytest.raises(CommandError, match="existing or privileged"):
        initialize_presenter_passwords(School.objects.get(pk=UNIVERSAL_SCHOOL_ID), operator_secrets)
    assert dict(UserAccount.objects.values_list("pk", "password")) == before
    login("teacher", operator_secrets)


@pytest.mark.parametrize("invalid", ["missing", "duplicate", "short", "whitespace", "control"])
def test_invalid_secrets_fail_before_provisioning(local_runtime, operator_secrets, monkeypatch, invalid):
    value = {"duplicate": operator_secrets["teacher"], "short": "short",
             "whitespace": " " + secrets.token_urlsafe(24),
             "control": secrets.token_urlsafe(24) + "\n"}.get(invalid, "")
    monkeypatch.setenv("CROWN_PRESENTER_PARENT_PASSWORD", value)
    with pytest.raises(CommandError) as error:
        prepare_presenter(apply=True, enable_password_login=True)
    assert not School.objects.exists()
    assert not UserAccount.objects.exists()
    assert not value or value not in str(error.value)


def test_default_seed_does_not_consume_or_enable_operator_secrets(local_runtime, operator_secrets):
    prepare_presenter(apply=True)
    assert all(not account.has_usable_password() for account in UserAccount.objects.all())
    response = APIClient().post("/api/v1/auth/token/", {
        "username": presenter_username("teacher"), "password": operator_secrets["teacher"],
    }, format="json")
    assert response.status_code == 401


def test_password_login_does_not_grant_revoked_role_or_foreign_tenant(local_runtime, operator_secrets):
    metrics = prepare_presenter(apply=True, enable_password_login=True)
    client, tokens = login("teacher", operator_secrets)
    teacher = UserAccount.objects.get(username=presenter_username("teacher"))
    UserRole.objects.filter(user=teacher, school_id=UNIVERSAL_SCHOOL_ID).delete()
    parent_client, _ = login("parent", operator_secrets)
    url = f"/api/v1/academics/sections/{metrics['teacher_section_id']}/assignments/"
    assert parent_client.post(url, {}, format="json").status_code == 403
    foreign = School.objects.create(name="Another fictional school")
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_SCHOOL_ID=str(foreign.pk))
    assert client.get(url).status_code == 404
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}", HTTP_X_SCHOOL_ID=str(UNIVERSAL_SCHOOL_ID))
    # A signed login is authentication; it cannot invent a persistent role.
    assert "TEACHER" not in client.get("/api/v1/dashboards/me/").json()["roles"]


def test_partial_initialization_rolls_back_without_rotating_any_account(local_runtime, operator_secrets):
    prepare_presenter(apply=True)
    teacher = UserAccount.objects.get(username=presenter_username("teacher"))
    teacher.set_password(secrets.token_urlsafe(32))
    teacher.save(update_fields=["password"])
    before = dict(UserAccount.objects.values_list("pk", "password"))
    with pytest.raises(CommandError, match="existing or privileged"):
        initialize_presenter_passwords(School.objects.get(pk=UNIVERSAL_SCHOOL_ID), operator_secrets)
    assert dict(UserAccount.objects.values_list("pk", "password")) == before
