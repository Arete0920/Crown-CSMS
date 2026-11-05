"""Regression tests for the opt-in fictional DEV childcare entitlement stage."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from core.models import School, UserAccount, UserRole
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import _SCHOOL_NAME
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite
from subscriptions.models import Feature, Plan, SchoolModule, TenantSubscription
from tenants.models import TenantProfile

SHA = "e" * 40
COMMAND = "provision_hosted_buyer_care_entitlements"
GUARD = "sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements._require_existing_dev_runtime"


@pytest.fixture
def buyer(db):
    school = School.objects.create(name=_SCHOOL_NAME, is_active=True)
    invite = SandboxInvite.objects.create(
        organization_label="Entirely fictional school evaluator",
        track="school",
        allowed_roles=["daycare_director"],
        allowed_seed_packs=["heritage-core"],
        expires_at=timezone.now() + timedelta(hours=1),
    )
    workspace = SandboxBuyerWorkspace.objects.create(
        invite=invite, school=school, source_sha=SHA, provisioned_at=timezone.now(),
    )
    username = buyer_username(school.id, "daycare_director")
    user = UserAccount.objects.create(
        username=username, email=username, school=school,
        is_active=True, is_staff=False, is_superuser=False,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])
    UserRole.objects.create(school=school, user=user, role_code="DAYCARE_DIRECTOR")
    return school, invite, workspace, user


def run(invite, *, apply=False, sha=SHA):
    out = StringIO()
    with patch(GUARD):
        with patch("sys.stdin", StringIO(str(invite.id) + "\n")):
            call_command(
                COMMAND, expected_sha=sha, invite_stdin=True,
                apply=apply, stdout=out,
            )
    return out.getvalue()


@pytest.mark.django_db
def test_default_is_read_only_and_does_not_enable_modules(buyer):
    school, invite, _, _ = buyer
    out = run(invite)
    assert "PRECHECK_ONLY" in out
    assert "release_certified=false" in out
    assert not TenantProfile.objects.filter(school=school).exists()
    assert not TenantSubscription.objects.filter(school_id=school.id).exists()
    assert not SchoolModule.objects.filter(school=school).exists()
    assert not Plan.objects.filter(code=f"buyer-care-{school.pk.hex}").exists()


@pytest.mark.django_db
def test_explicit_apply_is_school_isolated_and_repeat_denied(buyer):
    school, invite, _, _ = buyer
    other = School.objects.create(name="Unrelated genuine school", is_active=True)
    result = run(invite, apply=True)
    assert "FICTIONAL_ENTITLEMENTS_STAGED" in result
    assert "staff_clearance=NONE" in result
    assert "payments=OFF" in result
    tenant = TenantProfile.objects.get(school=school)
    assert tenant.status == "active"
    assert tenant.payment_provider == "none"
    sub = TenantSubscription.objects.get(school_id=school.id, ended_at__isnull=True)
    assert sub.is_trial
    assert sub.plan.code == f"buyer-care-{school.pk.hex}"
    assert sub.plan.entitlements.get(feature__key="diadem.daycare").enabled
    assert set(SchoolModule.objects.filter(school=school).values_list("module_key", flat=True)) == {
        "little_lambs", "before_care", "after_care",
    }
    assert not SchoolModule.objects.filter(school=other).exists()
    assert not TenantSubscription.objects.filter(school_id=other.id).exists()
    with pytest.raises(CommandError, match="Existing tenant or entitlement state"):
        run(invite, apply=True)
    assert TenantSubscription.objects.filter(school_id=school.pk).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", (
    "revoked", "expired", "source_drift", "renamed", "disabled",
    "uninvited", "role_revoked", "principal_disabled", "foreign_school",
))
def test_invalid_buyer_state_fails_without_entitlement_writes(buyer, mutation):
    school, invite, workspace, user = buyer
    if mutation == "revoked":
        invite.revoked_at = timezone.now()
        invite.save(update_fields=["revoked_at"])
    elif mutation == "expired":
        invite.expires_at = timezone.now() - timedelta(seconds=1)
        invite.save(update_fields=["expires_at"])
    elif mutation == "source_drift":
        workspace.source_sha = "a" * 40
        workspace.save(update_fields=["source_sha"])
    elif mutation == "renamed":
        school.name = "Real school"
        school.save(update_fields=["name"])
    elif mutation == "disabled":
        school.is_active = False
        school.save(update_fields=["is_active"])
    elif mutation == "uninvited":
        invite.allowed_roles = ["teacher"]
        invite.save(update_fields=["allowed_roles"])
    elif mutation == "role_revoked":
        UserRole.objects.filter(user=user, school=school).delete()
    elif mutation == "principal_disabled":
        user.is_active = False
        user.save(update_fields=["is_active"])
    elif mutation == "foreign_school":
        user.school = School.objects.create(name="Other", is_active=True)
        user.save(update_fields=["school"])
    with pytest.raises(CommandError):
        run(invite, apply=True)
    assert not TenantProfile.objects.filter(school=school).exists()
    assert not SchoolModule.objects.filter(school=school).exists()
    assert not Plan.objects.filter(code=f"buyer-care-{school.pk.hex}").exists()


@pytest.mark.django_db
def test_transaction_failure_rolls_back_plan_profile_feature_and_modules(buyer):
    school, invite, _, _ = buyer
    with patch(
        "sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements.SchoolModule.objects.create",
        side_effect=RuntimeError("simulated synthetic staging failure"),
    ):
        with pytest.raises(RuntimeError, match="simulated synthetic staging failure"):
            run(invite, apply=True)
    assert not Plan.objects.filter(code=f"buyer-care-{school.pk.hex}").exists()
    assert not TenantProfile.objects.filter(school=school).exists()
    assert not TenantSubscription.objects.filter(school_id=school.pk).exists()
    assert not SchoolModule.objects.filter(school=school).exists()
    assert not Feature.objects.filter(key="diadem.daycare").exists()


@pytest.mark.django_db
def test_existing_operational_tenant_cannot_be_repurposed(buyer):
    school, invite, _, _ = buyer
    TenantProfile.objects.create(school=school, slug="preexisting-tenant", status="active")
    with pytest.raises(CommandError, match="Existing tenant or entitlement state"):
        run(invite, apply=True)
    assert not SchoolModule.objects.filter(school=school).exists()
