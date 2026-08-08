from datetime import timedelta

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import CrownPermission, RolePermission, School, UserAccount
from core.permissions import user_has_permission
from sandbox_demo.catalog import (
    SANDBOX_PERSONAS,
    SANDBOX_SCHOOLS,
    SANDBOX_TRACKS,
    catalog_payload,
    get_school,
)
from sandbox_demo.models import SandboxInvite


class SandboxCatalogTests(SimpleTestCase):
    def test_catalog_exposes_only_heritage_christian_academy(self):
        self.assertEqual(list(SANDBOX_TRACKS), ["school"])
        self.assertEqual(list(SANDBOX_SCHOOLS), ["heritage-core"])

        payload = catalog_payload()
        self.assertEqual(len(payload["schools"]), 1)
        self.assertEqual(payload["schools"][0]["key"], "heritage-core")
        self.assertEqual(payload["schools"][0]["name"], "Heritage Christian Academy")

    def test_unknown_school_identifiers_fall_back_to_heritage(self):
        heritage = get_school("heritage-core")
        for value in [None, "heritage", "unknown-school-id", "legacy-school-key"]:
            self.assertEqual(get_school(value), heritage)


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

    @override_settings(
        CROWN_OPS_SECRET="test-ops-secret",
        CROWN_SANDBOX_ALLOW_OPEN_SESSION=False,
    )
    def test_invite_create_rejects_naive_expires_at(self):
        response = self.client.post(
            "/api/v1/sandbox/invites/",
            {
                "expires_at": "2026-07-06T12:00:00",
            },
            format="json",
            HTTP_X_CROWN_OPS_SECRET=self.ops_secret,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "sandbox_invite_expires_at_invalid")

    @override_settings(CROWN_OPS_SECRET="test-ops-secret")
    def test_invite_create_rejects_far_future_expires_at(self):
        response = self.client.post(
            "/api/v1/sandbox/invites/",
            {
                "expires_at": "2099-07-06T12:00:00+00:00",
            },
            format="json",
            HTTP_X_CROWN_OPS_SECRET=self.ops_secret,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "sandbox_invite_expires_at_invalid")

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

    @override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=True)
    def test_school_admin_session_self_heals_canonical_admissions_permission(self):
        RolePermission.objects.filter(
            role_code="HEAD_OF_SCHOOL",
            permission__code="admissions.view",
        ).delete()
        CrownPermission.objects.filter(code="admissions.view").delete()

        response = self.client.post(
            reverse("sandbox-session"),
            {"role": "school_admin", "school": "heritage", "track": "school"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        permission = CrownPermission.objects.get(code="admissions.view")
        self.assertTrue(
            RolePermission.objects.filter(
                role_code="HEAD_OF_SCHOOL",
                permission=permission,
            ).exists()
        )

        persona = SANDBOX_PERSONAS["school_admin"]
        user = UserAccount.objects.get(username=persona.email)
        school = School.objects.get(pk=response.json()["school_id"])
        self.assertTrue(user_has_permission(user, "admissions.view", school=school))

    @override_settings(CROWN_OPS_SECRET="test-ops-secret")
    def test_revoked_invite_blocks_session(self):
        invite = SandboxInvite.objects.create(
            organization_label="Heritage Christian Academy",
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
