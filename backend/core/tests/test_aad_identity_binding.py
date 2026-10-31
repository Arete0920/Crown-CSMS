"""Microsoft Entra immutable identity binding regression tests."""

import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIRequestFactory

from core.auth.aad_jwt import MicrosoftIdentityError, get_user_from_claims
from core.auth.authentication import AADBearerAuthentication
from core.models import School, UserRole
from integrations.models import MicrosoftIdentityLink, MicrosoftTenantBinding


pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_user(name: str):
    school = School.objects.create(name=name)
    user = User.objects.create_user(
        username=f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}@example.invalid",
        email=f"{uuid.uuid4().hex[:8]}@example.invalid",
        school=school,
        is_active=True,
    )
    return school, user


def _bind(*, school, user, tenant_id, object_id):
    binding = MicrosoftTenantBinding.objects.create(
        school=school,
        tenant_id=tenant_id,
        display_name=f"{school.name} Microsoft",
        is_active=True,
    )
    link = MicrosoftIdentityLink.objects.create(
        binding=binding,
        user=user,
        object_id=object_id,
        is_active=True,
    )
    return binding, link


def test_resolves_by_tid_oid_even_when_mutable_username_changes():
    tenant_id = uuid.uuid4()
    object_id = uuid.uuid4()
    school, user = _school_user("Immutable School")
    _bind(school=school, user=user, tenant_id=tenant_id, object_id=object_id)
    UserRole.objects.create(user=user, school=school, role_code="PARENT")

    claims = {
        "tid": str(tenant_id),
        "oid": str(object_id),
        "preferred_username": "renamed-user@example.invalid",
        "email": "different-address@example.invalid",
        "roles": ["GlobalAdministrator"],
    }

    resolved = get_user_from_claims(claims)

    assert resolved.pk == user.pk
    assert list(user.roles.values_list("role_code", flat=True)) == ["PARENT"]


def test_unprovisioned_tid_oid_fails_closed_without_creating_user():
    before = User.objects.count()

    with pytest.raises(MicrosoftIdentityError, match="not provisioned"):
        get_user_from_claims({"tid": str(uuid.uuid4()), "oid": str(uuid.uuid4())})

    assert User.objects.count() == before


@pytest.mark.parametrize("missing", ["tid", "oid"])
def test_required_immutable_claims_are_mandatory(missing):
    claims = {"tid": str(uuid.uuid4()), "oid": str(uuid.uuid4())}
    claims.pop(missing)

    with pytest.raises(MicrosoftIdentityError, match=missing):
        get_user_from_claims(claims)


def test_conflicting_same_tid_oid_mappings_fail_closed():
    tenant_id = uuid.uuid4()
    object_id = uuid.uuid4()
    school_a, user_a = _school_user("Shared Tenant A")
    school_b, user_b = _school_user("Shared Tenant B")
    _bind(school=school_a, user=user_a, tenant_id=tenant_id, object_id=object_id)
    _bind(school=school_b, user=user_b, tenant_id=tenant_id, object_id=object_id)

    with pytest.raises(MicrosoftIdentityError, match="ambiguous"):
        get_user_from_claims({"tid": str(tenant_id), "oid": str(object_id)})


def test_shared_tid_oid_may_map_multiple_schools_to_same_crown_user():
    tenant_id = uuid.uuid4()
    object_id = uuid.uuid4()
    school_a, user = _school_user("Shared Identity A")
    school_b = School.objects.create(name="Shared Identity B")
    UserRole.objects.create(user=user, school=school_b, role_code="TEACHER")
    _bind(school=school_a, user=user, tenant_id=tenant_id, object_id=object_id)
    _bind(school=school_b, user=user, tenant_id=tenant_id, object_id=object_id)

    resolved = get_user_from_claims({"tid": str(tenant_id), "oid": str(object_id)})

    assert resolved.pk == user.pk


def test_link_rejects_user_without_membership_in_bound_school():
    tenant_id = uuid.uuid4()
    object_id = uuid.uuid4()
    school_a, user = _school_user("Home School")
    school_b = School.objects.create(name="Foreign School")
    binding = MicrosoftTenantBinding.objects.create(
        school=school_b,
        tenant_id=tenant_id,
        is_active=True,
    )

    with pytest.raises(ValidationError, match="must belong to the bound CROWN school"):
        MicrosoftIdentityLink.objects.create(
            binding=binding,
            user=user,
            object_id=object_id,
            is_active=True,
        )


def test_inactive_school_binding_does_not_authenticate():
    tenant_id = uuid.uuid4()
    object_id = uuid.uuid4()
    school, user = _school_user("Inactive Entra School")
    _bind(school=school, user=user, tenant_id=tenant_id, object_id=object_id)
    school.is_active = False
    school.save(update_fields=["is_active"])

    with pytest.raises(MicrosoftIdentityError, match="not provisioned"):
        get_user_from_claims({"tid": str(tenant_id), "oid": str(object_id)})


def test_aad_authenticator_rejects_valid_but_unprovisioned_microsoft_identity():
    tenant_id = uuid.uuid4()
    object_id = uuid.uuid4()
    request = APIRequestFactory().get(
        "/api/iam/me/",
        HTTP_AUTHORIZATION="Bearer " + ("x" * 150),
    )
    authenticator = AADBearerAuthentication()

    with patch(
        "core.auth.authentication.decode_and_validate_bearer",
        return_value={"tid": str(tenant_id), "oid": str(object_id)},
    ):
        with pytest.raises(AuthenticationFailed, match="not provisioned"):
            authenticator.authenticate(request)


def test_aad_authenticator_fails_closed_on_identity_store_error():
    request = APIRequestFactory().get(
        "/api/iam/me/",
        HTTP_AUTHORIZATION="Bearer " + ("x" * 150),
    )
    authenticator = AADBearerAuthentication()

    with patch(
        "core.auth.authentication.decode_and_validate_bearer",
        return_value={"tid": str(uuid.uuid4()), "oid": str(uuid.uuid4())},
    ), patch(
        "core.auth.authentication.get_user_from_claims",
        side_effect=RuntimeError("synthetic identity store outage"),
    ):
        with pytest.raises(AuthenticationFailed, match="resolution unavailable"):
            authenticator.authenticate(request)
