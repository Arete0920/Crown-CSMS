"""Explicitly stage fictional childcare/Camp entitlements in an existing Azure DEV buyer school.

Read-only by default. No customer school, custody clearance, verified
qualification, commercial billing or external processor is modified.
"""
from __future__ import annotations

import sys
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from core.models import UserRole
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.management.commands.provision_hosted_buyer_workspace import (
    _INVITE, _SCHOOL_NAME, _require_existing_dev_runtime, _validate_invite,
)
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite
from subscriptions.models import Feature, Plan, PlanEntitlement, SchoolModule, TenantSubscription
from tenants.models import TenantProfile

_CARE_KEYS = ("little_lambs", "before_care", "after_care")
_CARE_ROLES = {"daycare_director": "DAYCARE_DIRECTOR", "daycare_staff": "DAYCARE_STAFF"}


def _checked_workspace(invite_id: str, expected_sha: str):
    """Require a bound active fictional school and real scoped buyer identities."""
    invite = SandboxInvite.objects.filter(pk=invite_id).first()
    roles = _validate_invite(invite)
    granted = [key for key in roles if key in _CARE_ROLES]
    if not granted:
        raise CommandError("An explicitly invited childcare role is required.")
    workspace = (
        SandboxBuyerWorkspace.objects.select_related("school").select_for_update()
        .filter(invite=invite).first()
    )
    if (
        workspace is None
        or workspace.source_sha != expected_sha
        or not workspace.school.is_active
        or workspace.school.name != _SCHOOL_NAME
        or str(workspace.school_id) == "19801b59-8c05-4c84-9312-5d792e4e839d"
    ):
        raise CommandError("An exact-source fictional buyer workspace is required.")
    for key in granted:
        if not UserRole.objects.filter(
            school=workspace.school,
            role_code=_CARE_ROLES[key],
            user__school=workspace.school,
            user__username=buyer_username(workspace.school_id, key),
            user__is_active=True,
            user__is_staff=False,
            user__is_superuser=False,
        ).exists():
            raise CommandError("Invited childcare principal and role must already exist.")
    return workspace


def _assert_empty(school):
    """Only initialize a fresh buyer school; never overwrite existing billing."""
    if (
        TenantProfile.objects.filter(school=school).exists()
        or TenantSubscription.objects.filter(school_id=school.pk).exists()
        or SchoolModule.objects.filter(school=school).exists()
        or Plan.objects.filter(code=f"buyer-care-{school.pk.hex}").exists()
    ):
        raise CommandError("Existing tenant or entitlement state requires separate review.")


class Command(BaseCommand):
    help = "Preflight or explicitly stage fictional buyer Daycare/AM-PM/Camp entitlements."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument("--invite-stdin", action="store_true", required=True)
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        _require_existing_dev_runtime(options["expected_sha"])
        raw = sys.stdin.readline(100).strip()
        if not _INVITE.fullmatch(raw):
            raise CommandError("Invalid invitation identifier format.")
        with transaction.atomic():
            workspace = _checked_workspace(raw, options["expected_sha"])
            school = workspace.school
            _assert_empty(school)
            if not options["apply"]:
                self.stdout.write(
                    "PRECHECK_ONLY: fictional_buyer=true; modules=daycare,care_am_pm,camp; "
                    "created=0; release_certified=false"
                )
                return

            # A buyer-specific plan cannot extend entitlements for other schools.
            plan = Plan.objects.create(
                code=f"buyer-care-{school.pk.hex}",
                name="Fictional buyer childcare evaluation",
                description="Synthetic Azure DEV demonstration, no commercial billing.",
                is_active=True,
            )
            feature, _ = Feature.objects.get_or_create(
                key="diadem.daycare", defaults={"name": "Diadem Daycare"}
            )
            PlanEntitlement.objects.create(plan=plan, feature=feature, enabled=True)
            TenantProfile.objects.create(
                school=school, slug=f"buyer-care-{school.pk.hex}",
                plan_code="starter", status="active", payment_provider="none",
            )
            TenantSubscription.objects.create(
                school_id=school.pk, plan=plan, started_at=timezone.now(), is_trial=True,
            )
            expires_at = timezone.now() + timedelta(days=7)
            for key in _CARE_KEYS:
                SchoolModule.objects.create(
                    school=school, module_key=key, status="active",
                    expiry_date=expires_at,
                    notes="Fictional invite-bound DEV proof only; not a license or policy attestation.",
                )

        self.stdout.write(
            self.style.SUCCESS(
                "FICTIONAL_ENTITLEMENTS_STAGED: modules=daycare,care_am_pm,camp; "
                "guardian_clearance=NONE; staff_clearance=NONE; payments=OFF; "
                "release_certified=false"
            )
        )
