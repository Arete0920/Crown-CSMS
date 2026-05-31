from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from sandbox_demo.models import SandboxAccessRequest, SandboxInvite


class SandboxAccessRequestWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.ops_secret = "test-ops-secret"

    def test_public_request_requires_tracking_consent(self):
        response = self.client.post(
            reverse("sandbox-access-request"),
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "work_email": "jane@example.org",
                "organization_name": "Example Christian Academy",
                "consent_demo_tracking": False,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "sandbox_request_consent_required")

    def test_public_request_creates_pending_request(self):
        response = self.client.post(
            reverse("sandbox-access-request"),
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "work_email": "JANE@EXAMPLE.ORG",
                "organization_name": "Example Christian Academy",
                "role_title": "Head of School",
                "school_type": "Christian K-12",
                "enrollment_size": "400-700",
                "primary_interest": "Tuition and billing",
                "preferred_demo_mode": "both",
                "consent_demo_tracking": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        item = SandboxAccessRequest.objects.get()
        self.assertEqual(item.status, "new")
        self.assertEqual(item.work_email, "jane@example.org")

    @override_settings(CROWN_OPS_SECRET="test-ops-secret")
    def test_ops_can_approve_request_and_create_invite(self):
        item = SandboxAccessRequest.objects.create(
            first_name="Jane",
            last_name="Smith",
            work_email="jane@example.org",
            organization_name="Example Christian Academy",
            consent_demo_tracking=True,
        )
        response = self.client.post(
            reverse("sandbox-access-request-decision", kwargs={"request_id": item.id, "decision": "approve"}),
            {"base_url": "https://app.example.org", "days": 7},
            format="json",
            HTTP_X_CROWN_OPS_SECRET=self.ops_secret,
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.status, "approved")
        self.assertIsNotNone(item.invite)
        self.assertIn("/sandbox?invite=", response.json()["url"])

    @override_settings(CROWN_OPS_SECRET="test-ops-secret")
    def test_ops_approve_rejects_invalid_days(self):
        invalid_payloads = [{}, {"days": "abc"}, {"days": -1}, {"days": 31}]
        for payload in invalid_payloads:
            item = SandboxAccessRequest.objects.create(
                first_name="Jane",
                last_name="Smith",
                work_email="jane@example.org",
                organization_name="Example Christian Academy",
                consent_demo_tracking=True,
            )
            response = self.client.post(
                reverse("sandbox-access-request-decision", kwargs={"request_id": item.id, "decision": "approve"}),
                {"base_url": "https://app.example.org", **payload},
                format="json",
                HTTP_X_CROWN_OPS_SECRET=self.ops_secret,
            )
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["code"], "sandbox_invite_days_invalid")
            item.refresh_from_db()
            self.assertEqual(item.status, "new")
            self.assertIsNone(item.invite)

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
