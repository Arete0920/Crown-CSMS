"""Provision an EMPTY fictional Azure DEV buyer workspace for an existing invite.

Defaults to read-only preflight. This command does not seed child, family,
custody, Aid or SGO records and never authorizes a buyer-facing release.
It can run only against the original CROWN DEV Azure PostgreSQL runtime.
"""
from __future__ import annotations

import re
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from core.models import School, UserAccount, UserRole
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.catalog import SANDBOX_PERSONAS
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_INVITE = re.compile(r"sbx_inv_[A-Za-z0-9]{1,24}\Z")
_AZURE_DEV_HOST = "crown-api-dev.azurewebsites.net"
_SCHOOL_NAME = "Heritage Christian Academy - Fictional Buyer Workspace"


def _require_existing_dev_runtime(expected_sha):
    """Fail closed on every production/local runtime and on source drift."""
    from os import environ

    actual_sha = str(getattr(settings, "BUILD_SHA", "") or "").strip()
    if not _SHA.fullmatch(expected_sha) or actual_sha != expected_sha:
        raise CommandError("Exact deployed source identity is required.")
    if (
        str(getattr(settings, "CROWN_ENV", "") or "").lower() != "dev"
        or str(getattr(settings, "DJANGO_ENV", "") or "").lower() not in {"", "dev"}
        or str(environ.get("AZURE_ENVIRONMENT", "") or "").lower() not in {"", "dev"}
        or environ.get("WEBSITE_HOSTNAME", "").strip().lower() != _AZURE_DEV_HOST
        or settings.DEBUG
        or getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", True)
        or getattr(settings, "CROWN_DEMO_MODE", False)
        or connection.vendor != "postgresql"
    ):
        raise CommandError("Only the existing isolated Azure DEV PostgreSQL runtime is allowed.")


def _validate_invite(invite):
    if invite is None or not invite.is_usable():
        raise CommandError("Invitation is missing, expired or revoked.")
    roles = invite.allowed_roles
    if (
        invite.track != "school"
        or invite.allowed_seed_packs != ["heritage-core"]
        or not isinstance(roles, list)
        or not roles
        or len(roles) != len(set(roles))
        or any(not isinstance(role, str) or role not in SANDBOX_PERSONAS for role in roles)
    ):
        raise CommandError("Invitation has an invalid, empty or expanding scope.")
    return roles


class Command(BaseCommand):
    help = "Preflight or explicitly provision an empty fictional Azure DEV buyer workspace."

    def add_arguments(self, parser):
        parser.add_argument("--expected-sha", required=True)
        parser.add_argument(
            "--invite-stdin", action="store_true", required=True,
            help="Read an existing invitation identifier only from stdin, never command-line arguments.",
        )
        parser.add_argument(
            "--apply", action="store_true",
            help="Explicitly create one synthetic school and its allowlisted user principals.",
        )

    def handle(self, *args, **options):
        _require_existing_dev_runtime(options["expected_sha"])
        raw = sys.stdin.readline(100).strip()
        if not _INVITE.fullmatch(raw):
            raise CommandError("Invalid invitation identifier format.")
        invite = SandboxInvite.objects.filter(pk=raw).first()
        roles = _validate_invite(invite)
        if SandboxBuyerWorkspace.objects.filter(invite=invite).exists():
            raise CommandError("Invitation already has a workspace; no reset or mutation allowed.")

        if not options["apply"]:
            self.stdout.write(
                f"PRECHECK_ONLY: permitted_roles={len(roles)}; "
                "no school, users or module records created; release_certified=false"
            )
            return

        # Lock before writing. A repeated or simultaneous invocation is refused.
        with transaction.atomic():
            locked = SandboxInvite.objects.select_for_update().get(pk=invite.pk)
            roles = _validate_invite(locked)
            if SandboxBuyerWorkspace.objects.filter(invite=locked).exists():
                raise CommandError("Invitation already provisioned. Operation not repeated.")
            _require_existing_dev_runtime(options["expected_sha"])

            school = School.objects.create(name=_SCHOOL_NAME, is_active=True)
            for key in roles:
                persona = SANDBOX_PERSONAS[key]
                username = buyer_username(school.id, key)
                account = UserAccount(
                    username=username,
                    email=username,
                    first_name=persona.first_name,
                    last_name=persona.last_name,
                    school=school,
                    is_active=True,
                    is_staff=False,
                    is_superuser=False,
                )
                account.set_unusable_password()
                account.save(force_insert=True)
                UserRole.objects.create(
                    school=school, user=account, role_code=persona.role_code
                )

            SandboxBuyerWorkspace.objects.create(
                invite=locked, school=school,
                source_sha=options["expected_sha"],
                provisioned_at=timezone.now(),
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"PROVISIONED_EMPTY: school_id={school.id}; permitted_roles={len(roles)}; "
                "module_fixtures=NONE; release_certified=false"
            )
        )
