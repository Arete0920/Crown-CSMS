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
from aftercare.daycare_release_models import DaycareRelease
from audit.models import AuditLog
from aftercare.daycare_release import release_child
from aftercare.daycare_checkin_models import DaycareAttendance, DaycareRoomStaffCoverage
from aftercare.daycare_models import (
    DaycareChild, DaycareEnrollment, DaycareGuardianAuthority,
    DaycareProgram, DaycareRoom, DaycareSite,
)
from core.models import School, UserAccount, UserRole
from households.models import Guardian, Household
from rest_framework.exceptions import PermissionDenied
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import _SCHOOL_NAME
from sandbox_demo.management.commands.seed_hosted_buyer_daycare import _HOUSEHOLD
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite, SandboxEvent
from subscriptions.models import Feature, Plan, PlanEntitlement, SchoolModule, TenantSubscription
from tenants.models import TenantProfile

SHA = "e" * 40
SEED = "seed_hosted_buyer_daycare"
ENTITLE = "provision_hosted_buyer_care_entitlements"
GUARD_SEED = "sandbox_demo.management.commands.seed_hosted_buyer_daycare._require_existing_dev_runtime"
GUARD_ENTITLE = "sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements._require_existing_dev_runtime"


def _create_buyer():
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


@pytest.fixture
def buyer(db):
    return _create_buyer()


@pytest.fixture
def transactional_buyer(transactional_db):
    return _create_buyer()


def run(invite, command=SEED, *, apply=False):
    guard = GUARD_SEED if command == SEED else GUARD_ENTITLE
    output = StringIO()
    with patch(guard), patch("sys.stdin", StringIO(str(invite.pk) + "\n")):
        call_command(command, expected_sha=SHA, invite_stdin=True, apply=apply, stdout=output)
    return output.getvalue()


@pytest.mark.django_db
def test_not_entitled_cannot_seed_or_preflight(buyer):
    school, invite, _, _ = buyer
    with pytest.raises(PermissionDenied, match="Active Diadem tenant required"):
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
    assert not Household.objects.filter(school_id=school.pk).exists()
    assert not SandboxEvent.objects.filter(invite=invite, event="fictional_daycare_custody_seeded").exists()

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
    persisted = DaycareRelease.objects.get(pk=released.pk)
    assert persisted.school_id == school.pk
    assert persisted.attendance_id == checked_in.pk
    assert persisted.guardian_authority_id == guardian.pk
    assert persisted.actor_id == staff.pk
    assert persisted.identity_verified is True
    assert DaycareAttendance.objects.get(pk=checked_in.pk).custody_release.pk == released.pk
    assert AuditLog.objects.filter(
        user_id=staff.pk, action="diadem.daycare.checkin", object_id=str(checked_in.pk),
    ).count() == 1
    assert AuditLog.objects.filter(
        user_id=staff.pk, action="diadem.daycare.release", object_id=str(released.pk),
    ).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("mutation", (
    "revoked", "expired", "source", "role", "director_role",
    "entitlement", "module_expired", "missing_director_invite",
    "staff_disabled", "tenant_suspended",
))
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
    elif mutation == "director_role":
        UserRole.objects.filter(user=principals["daycare_director"]).delete()
    elif mutation == "entitlement":
        module = SchoolModule.objects.get(school=school, module_key="little_lambs")
        module.status = "inactive"
        module.save(update_fields=["status"])
    elif mutation == "module_expired":
        SchoolModule.objects.filter(school=school, module_key="little_lambs").update(
            expiry_date=timezone.now() - timedelta(seconds=1),
        )
    elif mutation == "missing_director_invite":
        invite.allowed_roles = ["daycare_staff"]
        invite.save(update_fields=["allowed_roles"])
    elif mutation == "staff_disabled":
        UserAccount.objects.filter(pk=principals["daycare_staff"].pk).update(is_active=False)
    elif mutation == "tenant_suspended":
        TenantProfile.objects.filter(school=school).update(status="suspended")
    expected_error = (PermissionDenied if mutation in {
        "entitlement", "module_expired", "tenant_suspended"
    } else CommandError)
    with pytest.raises(expected_error):
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
    assert not Household.objects.filter(school_id=school.pk, name=_HOUSEHOLD).exists()
    assert not Guardian.objects.filter(school_id=school.pk).exists()
    assert not SandboxEvent.objects.filter(
        invite=invite, event="fictional_daycare_custody_seeded",
    ).exists()


@pytest.mark.django_db
def test_customer_plan_substitution_never_bypasses_buyer_module_expiry(buyer):
    school, invite, _, _ = buyer
    run(invite, ENTITLE, apply=True)
    ordinary = Plan.objects.create(
        code="fictional-bypass-probe", name="Test ordinary Daycare plan", is_active=True,
    )
    PlanEntitlement.objects.create(
        plan=ordinary, feature=Feature.objects.get(key="diadem.daycare"), enabled=True,
    )
    TenantSubscription.objects.filter(school_id=school.pk, ended_at__isnull=True).update(
        plan=ordinary,
    )
    SchoolModule.objects.filter(school=school, module_key="little_lambs").update(
        expiry_date=timezone.now() - timedelta(seconds=1),
    )
    with pytest.raises(CommandError, match="buyer-care subscription"):
        run(invite, apply=True)
    assert not DaycareSite.objects.filter(school=school).exists()
    assert not Household.objects.filter(school_id=school.pk, name=_HOUSEHOLD).exists()


@pytest.mark.django_db
def test_invalid_school_timezone_fails_read_only_preflight(buyer):
    school, invite, _, _ = buyer
    run(invite, ENTITLE, apply=True)
    school.timezone = "Invalid/Unrecognized_Timezone"
    school.save(update_fields=["timezone"])
    with pytest.raises(CommandError, match="timezone"):
        run(invite)
    assert not DaycareSite.objects.filter(school=school).exists()


@pytest.mark.django_db
def test_expired_buyer_module_blocks_admission_after_fixture_staging(buyer):
    school, invite, _, principals = buyer
    run(invite, ENTITLE, apply=True)
    run(invite, apply=True)
    SchoolModule.objects.filter(school=school, module_key="little_lambs").update(
        expiry_date=timezone.now() - timedelta(seconds=1),
    )
    site = DaycareSite.objects.get(school=school)
    room = DaycareRoom.objects.get(school=school)
    child = DaycareChild.objects.get(school=school)
    with pytest.raises(PermissionDenied):
        checkin_child(
            school_id=school.pk, actor_id=principals["daycare_staff"].pk,
            site_id=site.pk, room_id=room.pk, child_id=child.pk,
            program_code="DAYCARE", request_key=uuid4(),
        )
    assert not DaycareAttendance.objects.filter(school=school).exists()


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_fixture_writers_serialize(transactional_buyer):
    """Two independent database connections may stage only one custody fixture."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections, connections

    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL row locking is required for the concurrent fixture proof.")
    school, invite, _, _ = transactional_buyer
    run(invite, ENTITLE, apply=True)
    barrier = Barrier(2)

    class SharedFixedInvite:
        def readline(self, size=-1):
            return f"{invite.pk}\n"

    def attempt():
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_backend_pid()")
                backend_pid = cursor.fetchone()[0]
            barrier.wait(timeout=25)
            try:
                call_command(
                    SEED, expected_sha=SHA, invite_stdin=True,
                    apply=True, stdout=StringIO(),
                )
                return backend_pid, "created"
            except CommandError as exc:
                if "Existing school custody" not in str(exc):
                    raise
                return backend_pid, "denied_repeat"
        finally:
            connections.close_all()

    with patch(GUARD_SEED), patch("sys.stdin", SharedFixedInvite()):
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(attempt)
            second = pool.submit(attempt)
            outcomes = [first.result(timeout=65), second.result(timeout=65)]
    assert len({pid for pid, _ in outcomes}) == 2, outcomes
    assert sorted(status for _, status in outcomes) == ["created", "denied_repeat"]
    assert DaycareSite.objects.filter(school=school).count() == 1
    assert DaycareRoomStaffCoverage.objects.filter(school=school).count() == 1
    assert Household.objects.filter(school_id=school.pk, name=_HOUSEHOLD).count() == 1
    assert SandboxEvent.objects.filter(
        invite=invite, event="fictional_daycare_custody_seeded",
    ).count() == 1
