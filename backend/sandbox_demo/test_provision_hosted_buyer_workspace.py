"""Empty-workspace operator control: all DB tests are isolated synthetic SQLite.

The real Azure PostgreSQL runtime guard is independently enforced, never
bypassed for customer operations. No sample students or awards are seeded.
"""
from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from core.models import School, UserAccount, UserRole
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxEvent, SandboxInvite

SHA = "b" * 40
COMMAND = "sandbox_demo.management.commands.provision_hosted_buyer_workspace"


class HostedBuyerProvisionerTests(TestCase):
    def make_invite(self, roles=None):
        return SandboxInvite.objects.create(
            organization_label="Fictional institution",
            track="school",
            allowed_roles=["teacher", "parent"] if roles is None else roles,
            allowed_seed_packs=["heritage-core"],
            expires_at=timezone.now() + timedelta(days=1),
        )

    def execute(self, invite, *, apply=False):
        output = StringIO()
        arguments = ["--expected-sha", SHA, "--invite-stdin"]
        if apply:
            arguments.append("--apply")
        with patch("sys.stdin", StringIO(invite + "\n")):
            with patch(COMMAND + "._require_existing_dev_runtime"):
                call_command(COMMAND.rsplit(".", 1)[-1], *arguments, stdout=output)
        return output.getvalue()

    def test_dry_run_does_not_write_school_user_or_binding(self):
        invite = self.make_invite()
        result = self.execute(invite.id)
        self.assertIn("PRECHECK_ONLY", result)
        self.assertIn("release_certified=false", result)
        self.assertEqual(School.objects.count(), 0)
        self.assertEqual(UserAccount.objects.count(), 0)
        self.assertEqual(UserRole.objects.count(), 0)
        self.assertEqual(SandboxBuyerWorkspace.objects.count(), 0)
        self.assertEqual(SandboxEvent.objects.count(), 0)
        self.assertNotIn(invite.id, result)

    def test_explicit_apply_creates_isolated_empty_workspace_and_unusable_users(self):
        invite = self.make_invite()
        output = self.execute(invite.id, apply=True)
        self.assertIn("PROVISIONED_EMPTY", output)
        self.assertIn("module_fixtures=NONE", output)
        self.assertNotIn(invite.id, output)
        workspace = SandboxBuyerWorkspace.objects.get(invite=invite)
        self.assertEqual(workspace.source_sha, SHA)
        self.assertEqual(School.objects.count(), 1)
        self.assertEqual(UserRole.objects.filter(school=workspace.school).count(), 2)
        self.assertEqual(UserAccount.objects.filter(school=workspace.school).count(), 2)
        self.assertEqual(
            SandboxEvent.objects.filter(
                invite=invite, event="buyer_workspace_provisioned",
                school=str(workspace.school_id),
            ).count(),
            1,
        )
        for user in UserAccount.objects.filter(school=workspace.school):
            self.assertFalse(user.has_usable_password())
            self.assertFalse(user.is_staff)
            self.assertFalse(user.is_superuser)

    def test_two_invites_create_distinct_schools_and_global_usernames(self):
        first, second = self.make_invite(), self.make_invite()
        self.execute(first.id, apply=True)
        self.execute(second.id, apply=True)
        a = SandboxBuyerWorkspace.objects.get(invite=first)
        b = SandboxBuyerWorkspace.objects.get(invite=second)
        self.assertNotEqual(a.school_id, b.school_id)
        self.assertFalse(set(UserAccount.objects.filter(school=a.school).values_list("username", flat=True)) & set(
            UserAccount.objects.filter(school=b.school).values_list("username", flat=True)
        ))

    def test_repeat_apply_cannot_reset_an_existing_buyer_workspace(self):
        invite = self.make_invite()
        self.execute(invite.id, apply=True)
        state = list(UserAccount.objects.values_list("id", flat=True))
        with self.assertRaises(CommandError):
            self.execute(invite.id, apply=True)
        self.assertEqual(list(UserAccount.objects.values_list("id", flat=True)), state)
        self.assertEqual(SandboxBuyerWorkspace.objects.count(), 1)
        self.assertEqual(SandboxEvent.objects.filter(event="buyer_workspace_provisioned").count(), 1)

    def test_reject_expired_revoked_and_invalid_scope_without_writes(self):
        for kind in ("expired", "revoked", "empty", "foreign", "duplicated", "non_string"):
            invite = self.make_invite()
            if kind == "expired":
                invite.expires_at = timezone.now() - timedelta(seconds=1)
            elif kind == "revoked":
                invite.revoked_at = timezone.now()
            elif kind == "empty":
                invite.allowed_roles = []
            elif kind == "foreign":
                invite.allowed_seed_packs = ["not-heritage"]
            elif kind == "duplicated":
                invite.allowed_roles = ["teacher", "teacher"]
            elif kind == "non_string":
                invite.allowed_roles = [{"unsafe": "object"}]
            invite.save()
            with self.subTest(kind=kind):
                with self.assertRaises(CommandError):
                    self.execute(invite.id, apply=True)
        self.assertFalse(SandboxBuyerWorkspace.objects.exists())
        self.assertFalse(School.objects.exists())

    def test_nonmatching_input_is_denied_before_looking_up_invite(self):
        with self.assertRaises(CommandError):
            self.execute("../../../unexpected", apply=True)
        self.assertFalse(SandboxBuyerWorkspace.objects.exists())

    def test_unpatched_runtime_guard_rejects_local_sqlite(self):
        from sandbox_demo.management.commands.provision_hosted_buyer_workspace import (
            _require_existing_dev_runtime,
        )
        with self.assertRaises(CommandError):
            _require_existing_dev_runtime(SHA)
