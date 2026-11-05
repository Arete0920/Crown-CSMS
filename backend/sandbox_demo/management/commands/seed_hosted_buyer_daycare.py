"""Explicitly seed one *fictional* Daycare custody journey in an existing DEV buyer school.

The first call is read-only. --apply is a separately authorized mutation and
requires a previously granted, exact-source, invite-bound synthetic workspace
and the already staged time-limited Diadem entitlement. These synthetic policy
and identity assertions must NEVER be treated as real childcare clearances.
"""
from __future__ import annotations

import sys
from datetime import date, timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from aftercare.daycare_checkin import require_entitlement
from aftercare.daycare_checkin_models import DaycareRoomStaffCoverage
from aftercare.daycare_models import (
    DaycareChild, DaycareEnrollment, DaycareGuardianAuthority,
    DaycareProgram, DaycareRoom, DaycareSite,
)
from core.models import School, UserAccount
from households.models import Guardian, Household
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_care_entitlements import (
    _checked_workspace,
)
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import (
    _INVITE, _require_existing_dev_runtime,
)
from sandbox_demo.models import SandboxEvent

_HOUSEHOLD = "FICTIONAL DEMO ONLY - Daycare Household"
_SOURCE = "FICTIONAL TEST POLICY - NOT A REGULATORY OR LICENSING APPROVAL"
_QUALIFICATION = "FICTIONAL TEST STAFF QUALIFICATION - NO REAL CREDENTIAL"
_REQUIRED = frozenset(("daycare_director", "daycare_staff"))


def _principals(school, invite):
    if not isinstance(invite.allowed_roles, list) or not _REQUIRED.issubset(
        set(invite.allowed_roles)
    ):
        raise CommandError("Director and Staff must both be explicitly invited.")
    accounts = {}
    for key in sorted(_REQUIRED):
        try:
            accounts[key] = UserAccount.objects.select_for_update().get(
                username=buyer_username(school.pk, key),
                email=buyer_username(school.pk, key),
                school=school, is_active=True, is_staff=False, is_superuser=False,
            )
        except UserAccount.DoesNotExist as exc:
            raise CommandError("The exact-school fictional care principal is missing.") from exc
    if accounts["daycare_director"].pk == accounts["daycare_staff"].pk:
        raise CommandError("Independent fictional care principals required.")
    return accounts


def _empty_synthetic_care(school):
    """Never reset, alter, or silently share another scenario's custody data."""
    if (
        DaycareSite.objects.filter(school=school).exists()
        or DaycareRoom.objects.filter(school=school).exists()
        or DaycareChild.objects.filter(school=school).exists()
        or DaycareGuardianAuthority.objects.filter(school=school).exists()
        or DaycareRoomStaffCoverage.objects.filter(school=school).exists()
        or Household.objects.filter(school_id=school.pk, name=_HOUSEHOLD).exists()
    ):
        raise CommandError("Existing school custody/household records cannot be overwritten.")


class Command(BaseCommand):
    help = "Preflight or stage one invented, noncommercial Daycare acceptance journey."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument("--invite-stdin", action="store_true", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        expected_sha = options["expected_sha"]
        _require_existing_dev_runtime(expected_sha)
        invite_id = sys.stdin.readline(100).strip()
        if not _INVITE.fullmatch(invite_id):
            raise CommandError("Invalid invitation format.")

        with transaction.atomic():
            workspace = _checked_workspace(invite_id, expected_sha)
            school = School.objects.select_for_update().get(pk=workspace.school_id)
            if not school.is_active or workspace.source_sha != expected_sha:
                raise CommandError("Exact-source active fictional buyer school required.")
            director_and_staff = _principals(school, workspace.invite)
            # The real Daycare service checks the tenant, plan feature and
            # independently expiring buyer-school module; never bypass it.
            require_entitlement(school.pk)
            _empty_synthetic_care(school)

            if not options["apply"]:
                self.stdout.write(
                    "PRECHECK_ONLY: fictional_buyer=true; existing_care_rows=0; "
                    "release_certified=false; created=0"
                )
                return

            now = timezone.now()
            director = director_and_staff["daycare_director"]
            staff = director_and_staff["daycare_staff"]
            site = DaycareSite.objects.create(
                school=school, code="fictional-daycare", name="Fictional Demo Daycare",
                operating_mode="STANDALONE", jurisdiction="US-DE", is_active=True,
            )
            room = DaycareRoom.objects.create(
                school=school, site=site, code="fictional-room",
                name="Fictional Demonstration Room", is_active=True,
                licensed_capacity=4, max_children_per_staff=4,
                policy_source=_SOURCE, policy_verified_by=director,
                policy_verified_at=now,
            )
            household = Household.objects.create(
                school_id=school.pk, name=_HOUSEHOLD, is_active=True,
            )
            guardian = Guardian.objects.create(
                school_id=school.pk, household=household,
                first_name="Fictional", last_name="Guardian", is_primary=True,
            )
            child = DaycareChild.objects.create(
                school=school, site=site, household=household,
                first_name="Fictional", last_name="Child",
                date_of_birth=date(2022, 1, 15), is_active=True,
            )
            program = DaycareProgram.objects.create(
                school=school, site=site, code="DAYCARE",
                name="Fictional Daycare Program", is_active=True,
            )
            DaycareEnrollment.objects.create(
                school=school, site=site, child=child, program=program,
                room=room, status="ACTIVE", readiness="READY",
                start_date=timezone.localdate(now) - timedelta(days=1),
                end_date=timezone.localdate(now) + timedelta(days=7),
                weekdays=list(range(7)),
            )
            DaycareGuardianAuthority.objects.create(
                school=school, child=child, guardian=guardian,
                is_active=True, can_view=True, can_pickup=True,
                custody_status="CLEAR",
                verified_by=director, verified_at=now,
                effective_from=now - timedelta(hours=1),
                effective_until=now + timedelta(days=7),
            )
            DaycareRoomStaffCoverage.objects.create(
                school=school, site=site, room=room, staff=staff,
                starts_at=now - timedelta(hours=1),
                ends_at=now + timedelta(hours=8),
                is_active=True, is_qualified=True,
                qualification_evidence=_QUALIFICATION,
                verified_by=director, verified_at=now,
            )
            SandboxEvent.objects.create(
                invite=workspace.invite, event="fictional_daycare_custody_seeded",
                track="school", guidance="ops", persona="operator",
                school=str(school.pk), tour="", route="",
            )
        self.stdout.write(self.style.SUCCESS(
            "FICTIONAL_DAYCARE_STAGED: synthetic_child=1; simulated_policy=true; "
            "simulated_staff_clearance=true; synthetic_custody=true; "
            "payments=OFF; release_certified=false"
        ))
