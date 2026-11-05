"""PostgreSQL-compatible buyer-invitation isolation and denial contracts.

These tests deliberately use synthetic schools only. A passing test is
NOT hosted five-module application certification or invitation distribution.
"""
from __future__ import annotations

import uuid
from contextlib import nullcontext
from datetime import timedelta

from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import School, UserAccount, UserRole
from crown_api.jwt_utils import decode_access

from sandbox_demo.buyer_workspace import buyer_username
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.models import SandboxBuyerWorkspace, SandboxInvite, SandboxEvent

SHA = "a" * 40


@override_settings(
    DEBUG=False,
    CROWN_ENV="dev",
    BUILD_SHA=SHA,
    ALLOWED_HOSTS=["testserver"],
    CROWN_SANDBOX_ALLOW_OPEN_SESSION=False,
)
class HostedBuyerWorkspaceContract(TestCase):
    def make_invite(self, *, roles=None, expiry=None):
        return SandboxInvite.objects.create(
            organization_label="Fictional buyer evaluation",
            track="school",
            allowed_roles=roles if roles is not None else ["teacher"],
            allowed_seed_packs=["heritage-core"],
            expires_at=expiry or timezone.now() + timedelta(hours=1),
        )

    def make_workspace(self, invite, *, source=SHA, school_id=None, principal=True, role=True):
        school = School.objects.create(
            id=school_id or uuid.uuid4(),
            name="Heritage Christian Academy - Fictional Buyer",
            is_active=True,
        )
        space = SandboxBuyerWorkspace.objects.create(
            invite=invite,
            school=school,
            source_sha=source,
            provisioned_at=timezone.now(),
        )
        user = None
        if principal:
            name = buyer_username(school.id, "teacher")
            user = UserAccount.objects.create(
                username=name,
                email=name,
                school=school,
                is_active=True,
                is_staff=False,
                is_superuser=False,
            )
            user.set_unusable_password()
            user.save(update_fields=["password"])
            if role:
                UserRole.objects.create(school=school, user=user, role_code="TEACHER")
        return space, user

    def enter(self, invite=None, *, role="teacher", open_session=None, school="heritage-core"):
        client = APIClient()
        # Scope the override to this request. Deferring disable until
        # addCleanup() can restore a method-level CROWN_ENV override after
        # its decorator exits, leaking local mode into later hosted tests.
        setting_scope = (
            override_settings(CROWN_SANDBOX_ALLOW_OPEN_SESSION=open_session)
            if open_session is not None else nullcontext()
        )
        with setting_scope:
            return client.post(
                reverse("sandbox-session"),
                {"invite_id": invite.id if invite else None,
                 "role": role, "school": school, "track": "school"},
                format="json",
            )

    def test_explicit_daycare_director_invitation_is_school_scoped(self):
        """The director grant is per-invite, per-school, never the shared Heritage role."""
        invite = self.make_invite(roles=["daycare_director"])
        workspace, _ = self.make_workspace(invite, principal=False)
        username = buyer_username(workspace.school_id, "daycare_director")
        principal = UserAccount.objects.create(
            username=username, email=username, school=workspace.school,
            is_active=True, is_staff=False, is_superuser=False,
        )
        principal.set_unusable_password()
        principal.save(update_fields=["password"])
        UserRole.objects.create(
            user=principal, school=workspace.school, role_code="DAYCARE_DIRECTOR",
        )
        self.assertEqual(self.enter(invite, role="daycare_staff").status_code, 403)
        allowed = self.enter(invite, role="daycare_director")
        self.assertEqual(allowed.status_code, 201)
        self.assertEqual(allowed.data["route"], "/diadem/daycare/setup")
        self.assertEqual(allowed.data["role_code"], "DAYCARE_DIRECTOR")
        self.assertEqual(allowed.data["school_id"], str(workspace.school_id))
        self.assertEqual(allowed.data["refresh"], "")
        claims = decode_access(allowed.data["access"])
        self.assertTrue(claims.ok)
        self.assertEqual(claims.payload["sub"], str(principal.pk))
        self.assertEqual(claims.payload["school_id"], str(workspace.school_id))
        self.assertEqual(claims.payload["role"], "daycare_director")

    def test_internal_local_session_helper_rejects_hosted_roles(self):
        """Rehearsal code cannot bypass invite binding by invoking local token mint."""
        from sandbox_demo.services import create_sandbox_session

        for key in ("daycare_director", "daycare_staff"):
            with self.assertRaisesRegex(ValueError, "invite-owned workspace"):
                create_sandbox_session(
                    persona_key=key, school_key_or_id="heritage-core",
                    guidance="guided",
                )

    @override_settings(CROWN_ENV="")
    def test_local_open_mode_refuses_hosted_daycare_personas(self):
        """A local open sandbox cannot log in as a hosted-only buyer care role."""
        for role in ("daycare_director", "daycare_staff"):
            response = self.enter(role=role, open_session=True)
            self.assertEqual(response.status_code, 403, response.content[:300])
            self.assertEqual(
                response.data["code"], "sandbox_hosted_role_invite_required"
            )

    def test_uninvited_hosted_open_mode_cannot_access_shared_heritage(self):
        response = self.enter(open_session=True)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "sandbox_buyer_invite_required")
        self.assertEqual(SandboxEvent.objects.count(), 0)

    def test_unbound_invitation_never_issues_a_shared_school_session(self):
        invite = self.make_invite()
        response = self.enter(invite)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "sandbox_buyer_workspace_unprovisioned")
        invite.refresh_from_db()
        self.assertIsNone(invite.last_used_at)
        self.assertEqual(SandboxEvent.objects.count(), 0)

    def test_bound_school_requires_preprovisioned_principal_and_role(self):
        invite = self.make_invite()
        self.make_workspace(invite, principal=False)
        result = self.enter(invite)
        self.assertEqual(result.status_code, 403)
        self.assertEqual(result.data["code"], "sandbox_buyer_principal_unprovisioned")
        self.assertIsNone(SandboxInvite.objects.get(pk=invite.pk).last_used_at)

    def test_bound_school_denies_missing_role_grant(self):
        invite = self.make_invite()
        self.make_workspace(invite, role=False)
        self.assertEqual(self.enter(invite).data["code"], "sandbox_buyer_principal_unprovisioned")

    def test_hosted_scope_cannot_implicitly_expand_empty_or_foreign_packs(self):
        for roles, packs, expected_code in (
            ([], ["heritage-core"], "sandbox_buyer_invite_scope_invalid"),
            (["teacher"], [], "sandbox_buyer_invite_scope_invalid"),
            (["teacher"], ["heritage-core", "other-school"], "sandbox_buyer_invite_scope_invalid"),
            (["teacher"], ["other-school"], "sandbox_invite_school_not_allowed"),
        ):
            invite = self.make_invite(roles=roles)
            invite.allowed_seed_packs = packs
            invite.save(update_fields=["allowed_seed_packs"])
            self.make_workspace(invite)
            response = self.enter(invite)
            self.assertEqual(response.status_code, 403)
            self.assertEqual(response.data["code"], expected_code)
            self.assertIsNone(SandboxInvite.objects.get(pk=invite.pk).last_used_at)

    def test_wrong_invite_role_and_unknown_school_are_denied(self):
        invite = self.make_invite()
        self.make_workspace(invite)
        self.assertEqual(self.enter(invite, role="school_admin").status_code, 403)
        wrong_school = self.enter(invite, school="other-school")
        self.assertEqual(wrong_school.status_code, 400)
        self.assertEqual(wrong_school.data["code"], "sandbox_school_invalid")
        self.assertIsNone(SandboxInvite.objects.get(pk=invite.pk).last_used_at)

    def test_wrong_source_is_denied_even_if_school_and_role_exist(self):
        invite = self.make_invite()
        self.make_workspace(invite, source="b" * 40)
        self.assertEqual(self.enter(invite).data["code"], "sandbox_buyer_workspace_unverified")

    def test_shared_historical_heritage_school_cannot_be_bound(self):
        invite = self.make_invite()
        self.make_workspace(
            invite,
            school_id=uuid.UUID(SANDBOX_SCHOOLS["heritage-core"].id),
        )
        self.assertEqual(self.enter(invite).data["code"], "sandbox_buyer_workspace_unverified")

    def test_revoked_and_expired_invites_cannot_create_sessions(self):
        for revoked in (True, False):
            invite = self.make_invite(
                expiry=(timezone.now() + timedelta(minutes=15) if revoked
                        else timezone.now() - timedelta(seconds=1))
            )
            self.make_workspace(invite)
            if revoked:
                invite.revoked_at = timezone.now()
                invite.save(update_fields=["revoked_at"])
            self.assertEqual(self.enter(invite).status_code, 403)
            self.assertIsNone(SandboxInvite.objects.get(pk=invite.pk).last_used_at)

    def test_two_independent_buyers_get_distinct_signed_schools_and_principals(self):
        first, second = self.make_invite(), self.make_invite()
        one, one_user = self.make_workspace(first)
        two, two_user = self.make_workspace(second)
        self.assertNotEqual(one.school_id, two.school_id)
        self.assertNotEqual(one_user.username, two_user.username)
        a, b = self.enter(first), self.enter(second)
        self.assertEqual(a.status_code, 201)
        self.assertEqual(b.status_code, 201)
        self.assertNotEqual(a.data["school_id"], b.data["school_id"])
        for result, workspace, user in (
            (a, one, one_user), (b, two, two_user),
        ):
            self.assertEqual(result.data["school_id"], str(workspace.school_id))
            self.assertEqual(result.data["refresh"], "")
            claims = decode_access(result.data["access"])
            self.assertTrue(claims.ok)
            self.assertEqual(claims.payload["school_id"], str(workspace.school_id))
            self.assertEqual(claims.payload["sub"], str(user.pk))
            self.assertNotEqual(str(workspace.school_id), SANDBOX_SCHOOLS["heritage-core"].id)
        self.assertEqual(SandboxEvent.objects.count(), 2)
        self.assertIsNotNone(SandboxInvite.objects.get(pk=first.pk).last_used_at)
        self.assertIsNotNone(SandboxInvite.objects.get(pk=second.pk).last_used_at)

    def test_access_expiration_cannot_exceed_invite_expiry(self):
        invite = self.make_invite(expiry=timezone.now() + timedelta(seconds=70))
        self.make_workspace(invite)
        client = APIClient()
        result = client.post(
            reverse("sandbox-session"),
            {"invite_id": invite.id, "role": "teacher",
             "school": "heritage-core", "track": "school"},
            format="json",
        )
        self.assertEqual(result.status_code, 201)
        claims = decode_access(result.data["access"])
        self.assertTrue(claims.ok)
        self.assertLessEqual(claims.payload["exp"], int(invite.expires_at.timestamp()))
        self.assertLessEqual(claims.payload["exp"] - claims.payload["iat"], 900)
        # Django session authentication is also bound, not left at default
        # weeks-long expiry after the short signed buyer token expires.
        expiry = client.session.get_expiry_age()
        self.assertGreater(expiry, 0)
        self.assertLessEqual(expiry, 70)

    def test_invite_and_school_mappings_are_one_to_one(self):
        first, second = self.make_invite(), self.make_invite()
        workspace, _ = self.make_workspace(first)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                SandboxBuyerWorkspace.objects.create(
                    invite=second, school=workspace.school,
                    source_sha=SHA, provisioned_at=timezone.now(),
                )

    def test_hosted_mode_is_required_when_debug_is_misconfigured(self):
        invite = self.make_invite()
        with override_settings(DEBUG=True, CROWN_ENV="dev"):
            result = self.enter(invite)
        self.assertEqual(result.data["code"], "sandbox_buyer_workspace_unprovisioned")
