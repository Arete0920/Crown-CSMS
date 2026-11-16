"""Regression contract for the owner-retired hosted buyer access path.

This proves hosted enrollment and sessions remain unavailable even when old
Azure open-session flags or previously usable synthetic invitations exist.
The local legacy rehearsal remains governed by its separate existing tests.
"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from sandbox_demo.models import SandboxEvent, SandboxInvite


@override_settings(
    CROWN_ENV="dev", DEBUG=False,
    ALLOWED_HOSTS=["testserver"],
    CROWN_SALES_CONTROLLED_DEMO_ONLY=True,
    CROWN_SANDBOX_ALLOW_OPEN_SESSION=True,  # A stale DEV flag must not reopen access.
    CROWN_OPS_SECRET="synthetic-ops-only",
)
class RetiredHostedDemoAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_open_session_flag_cannot_authorize_hosted_visitor(self):
        response = self.client.post(
            reverse("sandbox-session"),
            {"role": "school_admin", "school": "heritage-core", "track": "school"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "sandbox_external_demo_retired")
        self.assertEqual(SandboxEvent.objects.count(), 0)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_existing_usable_invitation_cannot_start_or_resolve_session(self):
        invite = SandboxInvite.objects.create(
            organization_label="Invented legacy prospect",
            track="school", allowed_roles=["teacher"],
            allowed_seed_packs=["heritage-core"],
            expires_at=timezone.now() + timedelta(days=5),
        )
        session = self.client.post(
            reverse("sandbox-session"),
            {"invite_id": invite.pk, "role": "teacher",
             "school": "heritage-core", "track": "school"},
            format="json",
        )
        resolve = self.client.get(
            reverse("sandbox-invite-resolve", kwargs={"invite_id": invite.pk}),
        )
        self.assertEqual(session.status_code, 403)
        self.assertEqual(resolve.status_code, 403)
        self.assertEqual(session.data["code"], "sandbox_external_demo_retired")
        self.assertEqual(resolve.data["code"], "sandbox_external_demo_retired")
        invite.refresh_from_db()
        self.assertIsNone(invite.last_used_at)
        self.assertEqual(SandboxEvent.objects.count(), 0)

    def test_even_authorized_operator_cannot_create_external_invite(self):
        response = self.client.post(
            reverse("sandbox-invite-create"),
            {"days": 7, "allowed_roles": ["teacher"],
             "allowed_seed_packs": ["heritage-core"]},
            format="json",
            HTTP_X_CROWN_OPS_SECRET="synthetic-ops-only",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "sandbox_external_demo_retired")
        self.assertEqual(SandboxInvite.objects.count(), 0)

    def test_invitation_cli_denied_before_any_database_write(self):
        from io import StringIO
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaisesRegex(CommandError, "retired"):
            call_command(
                "sandbox_create_invite",
                organization="Invented operator", base_url="https://example.invalid",
                stdout=StringIO(),
            )
        self.assertEqual(SandboxInvite.objects.count(), 0)

    def test_hosted_guard_denies_buyer_identity_on_retired_setting(self):
        from sandbox_demo.buyer_workspace import hosted_self_service_retired
        self.assertTrue(hosted_self_service_retired())

    @override_settings(CROWN_ENV="local", CROWN_SANDBOX_ALLOW_OPEN_SESSION=False)
    def test_local_rehearsal_not_disabled_by_hosted_retirement(self):
        from sandbox_demo.buyer_workspace import hosted_self_service_retired
        with patch.dict("os.environ", {"WEBSITE_HOSTNAME": ""}):
            self.assertFalse(hosted_self_service_retired())
