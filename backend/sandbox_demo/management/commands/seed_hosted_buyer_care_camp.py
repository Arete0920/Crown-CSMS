"""Explicitly stage fictional AM/PM Care and BLOCKED Camp records in one DEV buyer.

No changes without --apply.  Requires a pre-existing, exact-SHA, invite-bound
school, canonical Jireh family/student and time-limited care entitlements.
Never stages genuine custody clearance, bills, payments or real-school data.
"""
from __future__ import annotations

import sys
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from aftercare.models import (
    AftercareAttendance, AftercareEnrollment, AftercarePickupContact,
    AftercareProgramConfig,
)
from aftercare.services import school_local_date
from core.models import School, Student as CoreStudent, UserAccount, UserRole
from core.permissions import user_has_permission
from households.models import Guardian as PortalGuardian, Student as PortalStudent
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements import (
    _checked_workspace,
)
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import (
    _INVITE, _require_existing_dev_runtime,
)
from sandbox_demo.models import SandboxBuyerAidFamily, SandboxEvent
from sandbox_demo.services import _seed_fictional_camp
from subscriptions.gates import school_has_module
from subscriptions.models import SchoolModule, TenantSubscription
from summer_camp.models import (
    SummerCampAttendance, SummerCampEnrollment, SummerCampProgram,
    SummerCampProgramConfig, SummerCampSession,
)

_EVENT = "fictional_buyer_care_camp_staged_v1"
_DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
_ROLES = {"parent": "PARENT", "school_admin": "HEAD_OF_SCHOOL"}
_MODULES = ("little_lambs", "before_care", "after_care")


def _require_personas(workspace):
    school = workspace.school
    invited = workspace.invite.allowed_roles
    if not isinstance(invited, list) or not set(_ROLES).issubset(invited):
        raise CommandError("Buyer parent and school administrator must both be invited.")
    accounts = {}
    for key, role in _ROLES.items():
        username = buyer_username(school.pk, key)
        account = UserAccount.objects.select_for_update().filter(
            school=school, username=username, email=username,
            is_active=True, is_staff=False, is_superuser=False,
        ).first()
        if account is None or not UserRole.objects.select_for_update().filter(
            school=school, user=account, role_code=role,
        ).exists():
            raise CommandError("Exact-school invited parent/admin authority required.")
        accounts[key] = account
    if not all(user_has_permission(accounts["school_admin"], name, school=school)
               for name in ("extended_care.view", "summer_camp.view")):
        raise CommandError("Existing school administrator view grants are required.")
    return accounts


def _require_canonical_buyer_child(workspace, parent):
    """Link to the exact Jireh-created portal household; never select by name alone."""
    school = workspace.school
    aid_link = SandboxBuyerAidFamily.objects.select_related(
        "family", "guardian",
    ).filter(workspace=workspace).first()
    if (aid_link is None or aid_link.family.school_id != school.pk
            or aid_link.guardian.school_id != school.pk
            or aid_link.guardian.family_id != aid_link.family_id
            or aid_link.guardian.email != parent.email):
        raise CommandError("An exact-school, already staged fictional Jireh family is required.")
    links = list(PortalGuardian.objects.select_related("household").select_for_update().filter(
        account=parent, school_id=school.pk, household__school_id=school.pk,
        household__is_active=True,
    )[:2])
    if len(links) != 1 or links[0].household.name != aid_link.family.family_name:
        raise CommandError("Canonical fictional buyer guardian/household link is invalid.")
    household = links[0].household
    children = list(PortalStudent.objects.select_for_update().filter(
        school_id=school.pk, household=household, is_active=True,
    )[:2])
    core_children = list(CoreStudent.objects.select_for_update().filter(
        school=school, family=aid_link.family, status="ACTIVE",
    )[:2])
    if (len(children) != 1 or len(core_children) != 1
            or (children[0].first_name, children[0].last_name) !=
               (core_children[0].first_name, core_children[0].last_name)):
        raise CommandError("Exactly one same-school fictional canonical student required.")
    return children[0]


def _require_fictional_modules(school):
    current = list(TenantSubscription.objects.select_related("plan").select_for_update()
                   .filter(school_id=school.pk, ended_at__isnull=True)[:2])
    if len(current) != 1 or current[0].plan.code != f"buyer-care-{school.pk.hex}" or not current[0].is_trial:
        raise CommandError("Exact-school noncommercial buyer-care trial required.")
    modules = list(SchoolModule.objects.select_for_update().filter(
        school=school, module_key__in=_MODULES,
    ))
    if len(modules) != len(_MODULES) or any(
        module.status != "active" or module.expiry_date is None
        or module.expiry_date <= timezone.now()
        or not school_has_module(school.pk, module.module_key)
        for module in modules
    ):
        raise CommandError("Active, unexpired buyer-school AM, PM and Camp entitlements required.")


def _require_unstaged(school, invite):
    """Never silently adopt, re-stage, renew or overwrite any existing scenario."""
    if (SandboxEvent.objects.filter(invite=invite, event=_EVENT, school=str(school.pk)).exists()
        or AftercareProgramConfig.objects.filter(school_fk=school).exists()
        or AftercareEnrollment.objects.filter(school_fk=school).exists()
        or AftercarePickupContact.objects.filter(school_fk=school).exists()
        or AftercareAttendance.objects.filter(school_fk=school).exists()
        or SummerCampProgramConfig.objects.filter(school=school).exists()
        or SummerCampProgram.objects.filter(school=school).exists()
        or SummerCampSession.objects.filter(school=school).exists()
        or SummerCampEnrollment.objects.filter(school=school).exists()
        or SummerCampAttendance.objects.filter(school=school).exists()):
        raise CommandError("Existing Care/Camp records require review; no reset or overwrite allowed.")


class Command(BaseCommand):
    help = "Preflight or explicitly stage fictional AM/PM and blocked Camp in an existing DEV buyer."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument("--invite-stdin", action="store_true", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        expected_sha = options["expected_sha"]
        _require_existing_dev_runtime(expected_sha)
        invite_id = sys.stdin.readline(100).strip()
        if not _INVITE.fullmatch(invite_id):
            raise CommandError("Invalid invitation identifier format.")
        with transaction.atomic():
            # _checked_workspace locks the exact invite and workspace and
            # checks DEV source, active ownership and existing childcare roles.
            workspace = _checked_workspace(invite_id, expected_sha)
            school = School.objects.select_for_update().get(pk=workspace.school_id, is_active=True)
            if school.pk != workspace.school_id:
                raise CommandError("Buyer school ownership changed.")
            actors = _require_personas(workspace)
            child = _require_canonical_buyer_child(workspace, actors["parent"])
            _require_fictional_modules(school)
            _require_unstaged(school, workspace.invite)
            # Require a valid school-local date even for read-only preflight.
            today = school_local_date(school.pk, timezone.now())
            if not options["apply"]:
                self.stdout.write(
                    "PRECHECK_ONLY: buyer_care_camp=true; existing_records=0; "
                    "created=0; release_certified=false"
                )
                return

            AftercareProgramConfig.objects.create(
                school_fk=school, late_fee_per_10_min=Decimal("0.00"),
                late_fee_cap=Decimal("0.00"),
            )
            for session in ("AM", "PM"):
                AftercareEnrollment.objects.create(
                    school_fk=school, student_fk=child, care_session=session,
                    start_date=today - timedelta(days=1), days_of_week=list(_DAYS),
                    billing_model="FLAT_MONTHLY", monthly_rate=Decimal("0.00"),
                    is_active=True,
                )
            AftercarePickupContact.objects.create(
                school_fk=school, student_fk=child, name="Fictional Guardian",
                relationship="FICTIONAL PARENT",
                notes="Synthetic test only; not real identity or custody clearance.",
            )
            # Existing canonical local fixture helper gains an explicitly
            # authorized buyer-workspace variant; never remove its local guard.
            evidence = _seed_fictional_camp(school, child, workspace=workspace)
            if (evidence["fictional_camp_sessions"] != 1
                    or evidence["fictional_camp_registrations"] != 1
                    or AftercareEnrollment.objects.filter(
                        school_fk=school, student_fk=child, is_active=True,
                        care_session__in=("AM", "PM"),
                    ).count() != 2):
                raise CommandError("Buyer Care/Camp staged-state verification failed.")
            SandboxEvent.objects.create(
                invite=workspace.invite, event=_EVENT, track="school",
                guidance="ops", persona="operator", school=str(school.pk),
                tour="", route="",
            )
        self.stdout.write(self.style.SUCCESS(
            "FICTIONAL_CARE_CAMP_STAGED: am=1; pm=1; camp_program=1; "
            "camp_registration=BLOCKED; payments=OFF; release_certified=false"
        ))
