"""Actual request-chain regression for hosted buyer revocation and tenant binding."""
from datetime import timedelta
import uuid

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import School, UserAccount, UserRole
from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite

SHA = "c" * 40


@override_settings(
    CROWN_ENV="dev", DEBUG=False, BUILD_SHA=SHA, ALLOWED_HOSTS=["testserver"],
    CROWN_SANDBOX_ALLOW_OPEN_SESSION=False,
)
class BuyerRevocationMiddlewareTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(
            id=uuid.uuid4(), name="Heritage Christian Academy - Fictional", is_active=True
        )
        self.invite = SandboxInvite.objects.create(
            organization_label="Fictional buyer",
            track="school", allowed_roles=["teacher"],
            allowed_seed_packs=["heritage-core"],
            expires_at=timezone.now() + timedelta(minutes=30),
        )
        self.workspace = SandboxBuyerWorkspace.objects.create(
            school=self.school, invite=self.invite, source_sha=SHA,
            provisioned_at=timezone.now(),
        )
        username = buyer_username(self.school.id, "teacher")
        self.user = UserAccount.objects.create(
            username=username, email=username, school=self.school,
            is_active=True, is_staff=False, is_superuser=False,
        )
        self.user.set_unusable_password()
        self.user.save(update_fields=["password"])
        self.role = UserRole.objects.create(
            user=self.user, school=self.school, role_code="TEACHER"
        )
        self.client = APIClient()

    def login(self):
        response = self.client.post(
            reverse("sandbox-session"),
            {"invite_id": self.invite.id, "role": "teacher",
             "school": "heritage-core", "track": "school"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content[:500])
        return response.data["access"]

    def check_blocked(self, *, token=None):
        kwargs = {"HTTP_AUTHORIZATION": "Bearer " + token} if token else {}
        response = self.client.get(reverse("sandbox-catalog"), **kwargs)
        self.assertEqual(response.status_code, 403, response.content[:500])
        self.assertEqual(response.json()["code"], "sandbox_buyer_session_invalid")

    def test_django_session_is_denied_immediately_after_invite_revoke(self):
        self.login()
        self.assertEqual(self.client.get(reverse("sandbox-catalog")).status_code, 200)
        self.invite.revoked_at = timezone.now()
        self.invite.save(update_fields=["revoked_at"])
        self.check_blocked()

    def test_bearer_token_is_denied_immediately_after_invite_revoke(self):
        token = self.login()
        self.invite.revoked_at = timezone.now()
        self.invite.save(update_fields=["revoked_at"])
        self.check_blocked(token=token)

    def test_school_disabled_blocks_existing_buyer_cookie(self):
        self.login()
        self.school.is_active = False
        self.school.save(update_fields=["is_active"])
        self.check_blocked()

    def test_user_role_revocation_blocks_existing_buyer_cookie(self):
        self.login()
        self.role.delete()
        self.check_blocked()

    def test_source_drift_blocks_existing_buyer_cookie(self):
        self.login()
        self.workspace.source_sha = "d" * 40
        self.workspace.save(update_fields=["source_sha"])
        self.check_blocked()

    def test_invite_expiry_blocks_existing_buyer_cookie(self):
        self.login()
        self.invite.expires_at = timezone.now() - timedelta(seconds=5)
        self.invite.save(update_fields=["expires_at"])
        self.check_blocked()

    def test_permitted_different_persona_does_not_reuse_current_session(self):
        self.login()
        self.invite.allowed_roles = ["parent"]
        self.invite.save(update_fields=["allowed_roles"])
        self.check_blocked()

    def test_regular_unauthenticated_public_catalog_stays_available(self):
        self.assertEqual(APIClient().get(reverse("sandbox-catalog")).status_code, 200)
