from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from sandbox_demo.models import SandboxInvite


class SandboxInviteWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ops_secret = "test-ops-secret"

    @override_settings(CROWN_OPS_SECRET="test-ops-secret")
    def test_ops_manual_invite_rejects_invalid_days(self):
        for payload in [{}, {"days": "abc"}, {"days": -1}, {"days": 31}]:
            response = self.client.post(
                reverse("sandbox-invite-create"),
                {"base_url": "https://app.example.org", **payload},
                format="json",
                HTTP_X_CROWN_OPS_SECRET=self.ops_secret,
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["code"], "sandbox_invite_days_invalid")

    @override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=False)
    def test_session_requires_invite_when_open_session_disabled(self):
        response = self.client.post(
            reverse("sandbox-session"),
            {"role": "school_admin", "school": "heritage", "track": "school"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "sandbox_invite_required")

    @override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=False)
    def test_missing_invite_returns_explicit_invite_required_code(self):
        response = self.client.post(
            reverse("sandbox-session"),
            {"role": "teacher", "school": "heritage", "track": "school"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "sandbox_invite_required")

    @override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
    def test_session_allows_missing_invite_only_when_open_session_enabled(self):
        response = self.client.post(
            reverse("sandbox-session"),
            {"role": "school_admin", "school": "heritage", "track": "school"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["school_id"], "19801b59-8c05-4c84-9312-5d792e4e839d")
        self.assertEqual(response.json()["role"], "school_admin")

    @override_settings(CROWN_OPS_SECRET="test-ops-secret")
    def test_revoked_invite_blocks_session(self):
        invite = SandboxInvite.objects.create(
            organization_label="Example Christian Academy",
            track="school",
            allowed_roles=["school_admin"],
            allowed_seed_packs=["heritage-core"],
            expires_at=timezone.now() + timedelta(days=7),
            revoked_at=timezone.now(),
        )
        response = self.client.post(
            reverse("sandbox-session"),
            {"invite_id": invite.id, "role": "school_admin", "school": "heritage-core", "track": "school"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["code"], "sandbox_invite_invalid")
