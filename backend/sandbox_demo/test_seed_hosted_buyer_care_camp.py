"""Offline Django regression proposal for an invite-owned synthetic Care/Camp stage.

These tests require the actual CROWN repository and Django test database.
They never connect to Azure or invoke real buyer provisioning.
"""
from contextlib import ExitStack
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import override_settings
from django.utils import timezone

from aftercare.models import AftercareEnrollment, AftercareAttendance, AftercareProgramConfig
from core.models import School, UserAccount, UserRole
from households.models import Student as PortalStudent
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import _SCHOOL_NAME
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite, SandboxEvent
from summer_camp.models import SummerCampProgram, SummerCampSession, SummerCampEnrollment
from subscriptions.models import SchoolModule

SHA = 'e' * 40
COMMAND = 'seed_hosted_buyer_care_camp'
GUARDS = (
    'sandbox_demo.management.commands.seed_hosted_jireh_buyer._require_existing_dev_runtime',
    'sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements._require_existing_dev_runtime',
    'sandbox_demo.management.commands.seed_hosted_buyer_daycare._require_existing_dev_runtime',
    'sandbox_demo.management.commands.seed_hosted_buyer_care_camp._require_existing_dev_runtime',
)
ROLES = {
    'parent': 'PARENT',
    'finance_director': 'FINANCE_DIRECTOR',
    'school_admin': 'HEAD_OF_SCHOOL',
    'daycare_director': 'DAYCARE_DIRECTOR',
    'daycare_staff': 'DAYCARE_STAFF',
}


def run(invite, command, *, apply=False, authorized=True):
    with ExitStack() as stack:
        for target in GUARDS:
            stack.enter_context(patch(target))
        stack.enter_context(patch(
            'sandbox_demo.management.commands.seed_hosted_buyer_care_camp.user_has_permission',
            return_value=authorized,
        ))
        stack.enter_context(patch('sys.stdin', StringIO(invite.pk + '\n')))
        output = StringIO()
        call_command(command, expected_sha=SHA, invite_stdin=True,
                     apply=apply, stdout=output)
        return output.getvalue()


@pytest.fixture
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def buyer(db):
    def create(*, seed_jireh=True):
        school = School.objects.create(name=_SCHOOL_NAME, is_active=True)
        invite = SandboxInvite.objects.create(
            organization_label='Invented isolated buyer',
            allowed_roles=list(ROLES), allowed_seed_packs=['heritage-core'],
            track='school', expires_at=timezone.now() + timedelta(hours=2),
        )
        workspace = SandboxBuyerWorkspace.objects.create(
            invite=invite, school=school, source_sha=SHA,
            provisioned_at=timezone.now(),
        )
        users = {}
        for key, role in ROLES.items():
            username = buyer_username(school.pk, key)
            user = UserAccount.objects.create(
                school=school, username=username, email=username,
                is_active=True, is_staff=False, is_superuser=False,
            )
            user.set_unusable_password()
            user.save(update_fields=['password'])
            UserRole.objects.create(school=school, user=user, role_code=role)
            users[key] = user
        # Reuse *existing* canonical, guarded hosted staging commands.
        if seed_jireh:
            run(invite, 'seed_hosted_jireh_buyer', apply=True)
        run(invite, 'provision_hosted_buyer_care_entitlements', apply=True)
        return school, invite, workspace, users
    return create


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_read_only_preflight_creates_no_care_or_camp_rows(buyer):
    school, invite, _, _ = buyer()
    output = run(invite, COMMAND)
    assert 'PRECHECK_ONLY' in output and 'created=0' in output
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()
    assert not AftercareProgramConfig.objects.filter(school_fk=school).exists()
    assert not SummerCampProgram.objects.filter(school=school).exists()
    assert not SummerCampSession.objects.filter(school=school).exists()


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_apply_stages_two_active_sessions_and_blocked_camp_without_payments(buyer):
    school, invite, _, _ = buyer()
    other, _, _, _ = buyer()
    output = run(invite, COMMAND, apply=True)
    assert 'FICTIONAL_CARE_CAMP_STAGED' in output
    assert 'payments=OFF' in output and 'release_certified=false' in output
    child = PortalStudent.objects.get(school_id=school.pk)
    enrollments = AftercareEnrollment.objects.filter(
        school_fk=school, student_fk=child, is_active=True,
    )
    assert set(enrollments.values_list('care_session', flat=True)) == {'AM', 'PM'}
    assert all(row.monthly_rate == 0 for row in enrollments)
    assert AftercareProgramConfig.objects.filter(school_fk=school).count() == 1
    assert not AftercareAttendance.objects.filter(school_fk=school).exists()
    assert SummerCampProgram.objects.filter(school=school).count() == 1
    assert SummerCampSession.objects.filter(school=school, status='PUBLISHED').count() == 1
    camp = SummerCampEnrollment.objects.get(school=school, student=child)
    assert camp.readiness_status == 'BLOCKED'
    assert camp.form_status == 'MISSING'
    assert camp.health_status == 'NEEDS_REVIEW'
    assert camp.payment_status == 'NOT_BILLED'
    assert camp.balance_due_cents == 0
    assert not SummerCampProgram.objects.filter(school=other).exists()
    assert not AftercareEnrollment.objects.filter(school_fk=other).exists()
    assert SandboxEvent.objects.filter(
        invite=invite, school=str(school.pk),
        event='fictional_buyer_care_camp_staged_v1',
    ).count() == 1
    with pytest.raises(CommandError, match='Existing Care/Camp records'):
        run(invite, COMMAND, apply=True)
    assert AftercareEnrollment.objects.filter(school_fk=school).count() == 2


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
@pytest.mark.parametrize('mutation', (
    'revoked', 'expired', 'source_drift', 'role_revoked',
    'permission_revoked', 'module_expired', 'trial_replaced', 'wrong_parent',
))
def test_invalid_scopes_fail_without_writes(buyer, mutation):
    school, invite, workspace, users = buyer()
    if mutation == 'revoked':
        invite.revoked_at = timezone.now()
        invite.save(update_fields=['revoked_at'])
    elif mutation == 'expired':
        invite.expires_at = timezone.now() - timedelta(seconds=1)
        invite.save(update_fields=['expires_at'])
    elif mutation == 'source_drift':
        workspace.source_sha = 'a' * 40
        workspace.save(update_fields=['source_sha'])
    elif mutation == 'role_revoked':
        UserRole.objects.filter(user=users['school_admin']).delete()
    elif mutation == 'module_expired':
        SchoolModule.objects.filter(school=school, module_key='after_care').update(
            expiry_date=timezone.now() - timedelta(seconds=1),
        )
    elif mutation == 'trial_replaced':
        from subscriptions.models import TenantSubscription
        TenantSubscription.objects.filter(school_id=school.pk).update(is_trial=False)
    elif mutation == 'wrong_parent':
        users['parent'].is_active = False
        users['parent'].save(update_fields=['is_active'])
    with pytest.raises(CommandError):
        run(invite, COMMAND, apply=True,
            authorized=(mutation != 'permission_revoked'))
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()
    assert not SummerCampProgram.objects.filter(school=school).exists()


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_second_buyer_cannot_reuse_first_buyers_records(buyer):
    first, invite_a, _, _ = buyer()
    second, invite_b, _, _ = buyer()
    run(invite_a, COMMAND, apply=True)
    run(invite_b, COMMAND, apply=True)
    assert AftercareEnrollment.objects.filter(school_fk=first).count() == 2
    assert AftercareEnrollment.objects.filter(school_fk=second).count() == 2
    assert SummerCampProgram.objects.filter(school=first).count() == 1
    assert SummerCampProgram.objects.filter(school=second).count() == 1
    ids_a = set(AftercareEnrollment.objects.filter(school_fk=first).values_list('student_fk_id', flat=True))
    ids_b = set(AftercareEnrollment.objects.filter(school_fk=second).values_list('student_fk_id', flat=True))
    assert ids_a.isdisjoint(ids_b)


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_injected_camp_failure_rolls_back_am_pm_enrollments(buyer):
    school, invite, _, _ = buyer()
    with patch(
        'sandbox_demo.management.commands.seed_hosted_buyer_care_camp._seed_fictional_camp',
        side_effect=RuntimeError('synthetic camp stage failure'),
    ):
        with pytest.raises(RuntimeError, match='synthetic camp stage failure'):
            run(invite, COMMAND, apply=True)
    assert not AftercareProgramConfig.objects.filter(school_fk=school).exists()
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()
    assert not SummerCampProgram.objects.filter(school=school).exists()
    assert not SandboxEvent.objects.filter(
        invite=invite, event='fictional_buyer_care_camp_staged_v1',
    ).exists()


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_distinct_daycare_and_jireh_households_are_not_adopted(buyer):
    from households.models import Household
    from aftercare.daycare_models import DaycareSite
    school, invite, _, _ = buyer()
    run(invite, 'seed_hosted_buyer_daycare', apply=True)
    assert Household.objects.filter(school_id=school.pk).count() == 2
    output = run(invite, COMMAND, apply=True)
    assert 'FICTIONAL_CARE_CAMP_STAGED' in output
    assert DaycareSite.objects.filter(school=school).count() == 1
    student = AftercareEnrollment.objects.get(school_fk=school, care_session='AM').student_fk
    assert student.household.name == 'Fictional Buyer Household'


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_missing_canonical_jireh_family_never_auto_created(buyer):
    from sandbox_demo.models import SandboxBuyerAidFamily
    school, invite, _, _ = buyer(seed_jireh=False)
    with pytest.raises(CommandError, match='fictional Jireh family'):
        run(invite, COMMAND, apply=True)
    assert not SandboxBuyerAidFamily.objects.filter(workspace__school=school).exists()
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()
    assert not SummerCampProgram.objects.filter(school=school).exists()


@pytest.mark.django_db
@override_settings(CROWN_HOSTED_JIREH_DEMO_ENABLED=True)
def test_existing_camp_program_is_never_adopted_or_overwritten(buyer):
    school, invite, _, _ = buyer()
    original = SummerCampProgram.objects.create(school=school, name='Existing separate school camp')
    with pytest.raises(CommandError, match='Existing Care/Camp records'):
        run(invite, COMMAND, apply=True)
    original.refresh_from_db()
    assert original.name == 'Existing separate school camp'
    assert not AftercareEnrollment.objects.filter(school_fk=school).exists()
