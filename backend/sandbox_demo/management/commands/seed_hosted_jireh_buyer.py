"""Opt-in, fictional-only Jireh fixture seeding for an EXISTING Azure DEV buyer.

No effect without --apply. A separate authorized operator must invoke it.
Does not grant real SGO membership or create any payment/award/commitment.
"""
from __future__ import annotations

import re
import sys
from datetime import date

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import AcademicYear, Family, Guardian, School, Student, UserAccount
from jireh_sgo.models import (
    SGOFamilyGrant, SGOOrganization, SGOProcessorAssignment, SGOProgram,
)
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.models import (
    SandboxBuyerAidFamily, SandboxBuyerSGOPartner,
    SandboxBuyerSGOProgram, SandboxBuyerWorkspace,
)
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import (
    _require_existing_dev_runtime, _validate_invite,
)

_INVITE = re.compile(r"sbx_inv_[A-Za-z0-9]{1,24}\Z")


class Command(BaseCommand):
    help = "Preflight or explicitly seed invented Jireh buyer-school / partner fixtures."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument("--invite-stdin", action="store_true", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        _require_existing_dev_runtime(options["expected_sha"])
        if not getattr(settings, "CROWN_HOSTED_JIREH_DEMO_ENABLED", False):
            raise CommandError("Hosted Jireh fictional demonstration is disabled.")
        raw = sys.stdin.readline(100).strip()
        if not _INVITE.fullmatch(raw):
            raise CommandError("Invalid invitation input.")
        workspace = (
            SandboxBuyerWorkspace.objects.select_related("school", "invite")
            .filter(invite_id=raw).first()
        )
        if workspace is None or not workspace.invite.is_usable():
            raise CommandError("Existing authorized workspace required.")
        roles = _validate_invite(workspace.invite)
        if "parent" not in roles:
            raise CommandError("The invitation has no fictional family role.")
        if workspace.source_sha != options["expected_sha"] or str(workspace.school_id) == SANDBOX_SCHOOLS["heritage-core"].id:
            raise CommandError("Workspace source or historical school is invalid.")
        if not workspace.school.is_active:
            raise CommandError("Workspace school inactive.")
        if not UserAccount.objects.filter(
            username=buyer_username(workspace.school_id, "parent"),
            school_id=workspace.school_id, is_active=True, is_staff=False,
            is_superuser=False,
        ).exists():
            raise CommandError("Pre-provisioned fictional parent principal required.")
        if (
            SandboxBuyerAidFamily.objects.filter(workspace=workspace).exists()
            or SandboxBuyerSGOPartner.objects.filter(workspace=workspace).exists()
            or AcademicYear.objects.filter(school=workspace.school).exists()
            or Family.objects.filter(school=workspace.school).exists()
            or Guardian.objects.filter(school=workspace.school).exists()
            or Student.objects.filter(school=workspace.school).exists()
        ):
            raise CommandError("Not an empty fictional buyer workspace; no reset or overwrite allowed.")
        if not options["apply"]:
            self.stdout.write("PRECHECK_ONLY: no fixture changes; release_certified=false")
            return

        with transaction.atomic():
            workspace = SandboxBuyerWorkspace.objects.select_related(
                "school", "invite"
            ).select_for_update().get(pk=workspace.pk)
            School.objects.select_for_update().get(pk=workspace.school_id, is_active=True)
            _require_existing_dev_runtime(options["expected_sha"])
            if not workspace.invite.is_usable() or workspace.source_sha != options["expected_sha"]:
                raise CommandError("Workspace authority expired or changed.")
            if (
                SandboxBuyerAidFamily.objects.filter(workspace=workspace).exists()
                or SandboxBuyerSGOPartner.objects.filter(workspace=workspace).exists()
                or Family.objects.filter(school=workspace.school).exists()
                or Student.objects.filter(school=workspace.school).exists()
                or AcademicYear.objects.filter(school=workspace.school).exists()
            ):
                raise CommandError("Existing buyer module records are never overwritten.")

            parent = UserAccount.objects.select_for_update().get(
                username=buyer_username(workspace.school_id, "parent"),
                school=workspace.school,
            )
            if parent.guardian_id:
                raise CommandError("Parent account is already linked to a guardian.")
            year = AcademicYear.objects.create(
                school=workspace.school,
                name="2026-2027 (invented buyer scenario)",
                start_date=date(2026, 8, 1),
                end_date=date(2027, 6, 30),
                is_current=True,
            )
            family = Family.objects.create(
                school=workspace.school, family_name="Fictional Buyer Household",
            )
            guardian = Guardian.objects.create(
                school=workspace.school, family=family, first_name="Example",
                last_name="Guardian", email=parent.email,
                relationship="MOTHER", portal_access=True, custody_flag=False,
            )
            student = Student.objects.create(
                school=workspace.school, family=family,
                student_number=f"FICTIONAL-{workspace.school_id.hex[:16]}",
                first_name="Example", last_name="Student", dob=date(2013, 3, 1),
                status="ACTIVE",
            )
            parent.guardian = guardian
            parent.save(update_fields=["guardian"])
            SandboxBuyerAidFamily.objects.create(
                workspace=workspace, family=family, guardian=guardian,
            )

            for state, state_name in (("DE", "Delaware"), ("PA", "Pennsylvania")):
                organization = SGOOrganization.objects.create(
                    legal_name=f"Fictional External {state_name} SGO (buyer test)",
                    state_of_domicile=state, active=True,
                )
                partner = SandboxBuyerSGOPartner.objects.create(
                    workspace=workspace, organization=organization,
                )
                program = SGOProgram.objects.create(
                    organization=organization, name=f"Fictional {state} Partner 2026",
                    code=f"fictional-partner-{state.lower()}", calendar_year=2026,
                    funding_source=SGOProgram.PRIVATE,
                    eligibility_rule_version=f"FICTIONAL_{state}_2026_V1",
                )
                SandboxBuyerSGOProgram.objects.create(
                    partner=partner, program=program,
                )
                SGOFamilyGrant.objects.create(
                    program=program, user=parent, student_key=student.pk,
                    school_key=workspace.school_id, consent_version=f"FICTIONAL_{state}_CONSENT_V1",
                    active=True,
                )
                # Processor authority is explicit and scoped only to the invented
                # program. Do not grant an SGO organization membership or award role.
                for role in ("finance_director", "school_admin"):
                    if role in roles:
                        processor = UserAccount.objects.get(
                            username=buyer_username(workspace.school_id, role),
                            school=workspace.school,
                        )
                        SGOProcessorAssignment.objects.create(
                            program=program, user=processor, active=True,
                        )
        self.stdout.write(
            "FICTIONAL_JIREH_FIXTURES_CREATED: buyer school, one household, "
            "two independent external partners and programs; release_certified=false"
        )
