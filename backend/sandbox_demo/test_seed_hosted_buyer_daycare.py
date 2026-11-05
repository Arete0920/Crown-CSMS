"""Fail-closed tests for the DEV-only, invite-bound fictional custody fixture."""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone

from aftercare.daycare_checkin import checkin_child
from aftercare.daycare_release import release_child
from aftercare.daycare_checkin_models import DaycareAttendance, DaycareRoomStaffCoverage
from aftercare.daycare_models import (
    DaycareChild, DaycareEnrollment, DaycareGuardianAuthority,
    DaycareProgram, DaycareRoom, DaycareSite,
)
from core.models import School, UserAccount, UserRole
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import _SCHOOL_NAME
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite, SandboxEvent
from subscriptions.models import SchoolModule

SHA = "e" * 40
SEED = "seed_hosted_buyer_daycare"
ENTITLE = "provision_hosted_buyer_care_entitlements"
GUARD_SEED = "sandbox_demo.management.commands.seed_hosted_buyer_daycare._require_existing_dev_runtime"
GUARD_ENTITLE = "sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements._require_existing_dev_runtime"


@pytest.fixture
def buyer(db):
    school = School.objects.create(name=_SCHOOL_NAME, is_active=True)
    invite = SandboxInvite.objects.create(
        organization_label="Fictional Daycare buyer",
        track="school",
        allowed_roles=["daycare_director", "daycare_staff"],
        allowed_seed_packs=["heritage-core"],
        expires_at=timezone.now() + timedelta(hours=2),
    )
    workspace = SandboxBuyerWorkspace.objects.create(
        invite=invite, school=school, source_sha=SHA, provisioned_at=timezone.now(),
    )
    principals = {}
    for key, role in (("daycare_director", "DAYCARE_DIRECTOR"), ("daycare_staff", "DAYCARE_STAFF")):
        username = buyer_username(school.pk, key)
        principal = UserAccount.objects.create(
            school=school, username=username, email=username,
            is_active=True, is_staff=False, is_superuser=False,
        )
        principal.set_unusable_password()
        principal.save(update_fields=["password"])
        UserRole.objects.create(school=school, user=principal, role_code=role)
        principals[key] = principal
    return school, invite, workspace, principals


def run(invite, command=SEED, *, apply=False):
    guard = GUARD_SEED if command == SEED else GUARD_ENTITLE
    output = StringIO()
    with patch(guard), patch("sys.stdin", StringIO(str(invite.pk) + "\n")):
        call_command(command, expected_sha=SHA, invite_stdin=True, apply=apply, stdout=output)
    return output.getvalue()


@pytest.mark.django_db
def test_not_entitled_cannot_seed_or_preflight(buyer):
    school, invite, _, _ = buyer
    with pytest.raises(Exception):
        run(invite)
    assert not DaycareSite.objects.filter(school=school).exists()
    assert not DaycareRoomStaffCoverage.objects.filter(school=school).exists()


@pytest.mark.django_db
def test_preflight_is_read_only_then_apply_is_one_time_and_isolated(buyer):
    school, invite, _, _ = buyer
    other = School.objects.create(name="Unrelated operational school", is_active=True)
    run(invite, ENTITLE, apply=True)
    result = run(invite)
    assert "PRECHECK_ONLY" in result and "created=0" in result
    assert not DaycareSite.objects.filter(school=school).exists()

    result = run(invite, apply=True)
    assert "FICTIONAL_DAYCARE_STAGED" in result
    assert "release_certified=false" in result
    assert DaycareSite.objects.filter(school=school).count() == 1
    assert DaycareRoom.objects.filter(school=school, is_active=True).count() == 1
    assert DaycareChild.objects.filter(school=school, is_active=True).count() == 1
    assert DaycareEnrollment.objects.filter(school=school, status="ACTIVE", readiness="READY").count() == 1
    assert DaycareGuardianAuthority.objects.filter(school=school, is_active=True, custody_status="CLEAR").count() == 1
    assert DaycareRoomStaffCoverage.objects.filter(school=school, is_active=True).count() == 1
    assert not DaycareSite.objects.filter(school=other).exists()
    assert not DaycareGuardianAuthority.objects.filter(school=other).exists()
    assert SandboxEvent.objects.filter(invite=invite, event="fictional_daycare_custody_seeded").count() == 1
    with pytest.raises(CommandError, match="Existing school custody"):
        run(invite, apply=True)


@pytest.mark.django_db
def test_authenticated_care_service_can_checkin_and_release_only_synthetic_child(buyer):
    school, invite, _, principals = buyer
    run(invite, ENTITLE, apply=True)
    run(invite, apply=True)
    site = DaycareSite.objects.get(school=school)
    room = DaycareRoom.objects.get(school=school)
    child = DaycareChild.objects.get(school=school)
    guardian = DaycareGuardianAuthority.objects.get(school=school)
    staff = principals["daycare_staff"]
    checked_in = checkin_child(
        school_id=school.pk, actor_id=staff.pk, site_id=site.pk,
        room_id=room.pk, child_id=child.pk, program_code="DAYCARE",
        request_key=uuid4(),
    )
    assert DaycareAttendance.objects.filter(pk=checked_in.pk, custody_release__isnull=True).exists()
    released = release_child(
        school_id=school.pk, actor_id=staff.pk, site_id=site.pk,
        room_id=room.pk, attendance_id=checked_in.pk,
        guardian_authority_id=guardian.pk, request_key=uuid4(),
        identity_verified=True, identity_method="PERSONALLY_KNOWN",
    )
    assert released.attendance_id == checked_in.pk
    assert not DaycareAttendance.objects.filter(
        pk=checked_in.pk, custody_release__isnull=True,
    ).exists()


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", ("revoked", "expired", "source", "role", "entitlement"))
def test_revoked_or_unscoped_workspace_never_seeds_custody(buyer, mutation):
    school, invite, workspace, principals = buyer
    run(invite, ENTITLE, apply=True)
    if mutation == "revoked":
        invite.revoked_at = timezone.now()
        invite.save(update_fields=["revoked_at"])
    elif mutation == "expired":
        invite.expires_at = timezone.now() - timedelta(seconds=1)
        invite.save(update_fields=["expires_at"])
    elif mutation == "source":
        workspace.source_sha = "a" * 40
        workspace.save(update_fields=["source_sha"])
    elif mutation == "role":
        UserRole.objects.filter(user=principals["daycare_staff"]).delete()
    elif mutation == "entitlement":
        module = SchoolModule.objects.get(school=school, module_key="little_lambs")
        module.status = "inactive"
        module.save(update_fields=["status"])
    with pytest.raises(Exception):
        run(invite, apply=True)
    assert not DaycareSite.objects.filter(school=school).exists()


@pytest.mark.django_db
def test_injected_failure_rolls_back_entire_synthetic_custody_fixture(buyer):
    school, invite, _, _ = buyer
    run(invite, ENTITLE, apply=True)
    with patch(
        "sandbox_demo.management.commands.seed_hosted_buyer_daycare.DaycareRoomStaffCoverage.objects.create",
        side_effect=RuntimeError("simulated coverage insert failure"),
    ):
        with pytest.raises(RuntimeError, match="simulated coverage insert failure"):
            run(invite, apply=True)
    for model in (DaycareSite, DaycareRoom, DaycareChild, DaycareEnrollment,
                  DaycareProgram, DaycareGuardianAuthority, DaycareRoomStaffCoverage):
        assert not model.objects.filter(school=school).exists()
    assert not SandboxEvent.objects.filter(
        invite=invite, event="fictional_daycare_custody_seeded",
    ).exists()
