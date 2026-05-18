"""Phase 3B-B controlled onboarding consumption proof tests."""

import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import School
from solomon.models import (
    SolomonAudience,
    SolomonCategory,
    SolomonContextRule,
    SolomonLifecycle,
    SolomonPlaybook,
    SolomonResource,
    SolomonResourceType,
    SolomonScope,
    SolomonVisibility,
)

User = get_user_model()


class ParentEnrollmentGuidanceSurfaceTests(TestCase):
    def setUp(self):
        self.school_a = School.objects.create(name=f"Guidance School A {uuid.uuid4().hex[:6]}")
        self.school_b = School.objects.create(name=f"Guidance School B {uuid.uuid4().hex[:6]}")
        self.user = User.objects.create_user(
            username=f"guidance_user_{uuid.uuid4().hex[:6]}",
            password="pass",
        )

    def _authed_client(self, school):
        token = str(RefreshToken.for_user(self.user).access_token)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_SCHOOL_ID=str(school.id))
        return client

    def _build_parent_enrollment_context(self):
        category = SolomonCategory.objects.create(
            name=f"Enrollment {uuid.uuid4().hex[:6]}",
            slug=f"enrollment-{uuid.uuid4().hex[:8]}",
            is_public=True,
        )
        audience = SolomonAudience.objects.create(
            name=f"Parent {uuid.uuid4().hex[:6]}",
            slug=f"parent-{uuid.uuid4().hex[:8]}",
            role_code="parent",
            is_public=True,
        )

        resource = SolomonResource.objects.create(
            title="Parent Enrollment Guide",
            slug=f"parent-enrollment-guide-{uuid.uuid4().hex[:8]}",
            category=category,
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.SCHOOL,
            module="onboarding",
            route_path="/students/enrollment",
        )
        resource.audiences.add(audience)

        playbook = SolomonPlaybook.objects.create(
            title="Parent Enrollment Playbook",
            slug=f"parent-enrollment-playbook-{uuid.uuid4().hex[:8]}",
            summary="Parent enrollment steps",
            module="onboarding",
            route_path="/students/enrollment",
            category=category,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
        )
        playbook.audiences.add(audience)

        SolomonContextRule.objects.create(
            module="onboarding",
            route_path="/students/enrollment",
            context_key="parent-enrollment",
            audience=audience,
            resource=resource,
            playbook=playbook,
            is_active=True,
        )

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_progress_can_include_parent_enrollment_guidance(self):
        self._build_parent_enrollment_context()
        client = self._authed_client(self.school_a)

        res = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("parent_enrollment_guidance", data)
        guidance = data["parent_enrollment_guidance"]
        self.assertEqual(guidance["status"], "resolved")
        self.assertIsInstance(guidance["resources"], list)
        self.assertIsInstance(guidance["playbooks"], list)
        self.assertIsInstance(guidance["context_rules"], list)

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_progress_guidance_is_deterministic(self):
        self._build_parent_enrollment_context()
        client = self._authed_client(self.school_a)

        res1 = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )
        res2 = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(
            res1.json().get("parent_enrollment_guidance"),
            res2.json().get("parent_enrollment_guidance"),
        )

    @override_settings(CROWN_SOLOMON_API_ENABLED=False, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_progress_is_silent_noop_when_api_flag_disabled(self):
        self._build_parent_enrollment_context()
        client = self._authed_client(self.school_a)

        res = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertNotIn("parent_enrollment_guidance", res.json())

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=False)
    def test_progress_is_silent_noop_when_context_flag_disabled(self):
        self._build_parent_enrollment_context()
        client = self._authed_client(self.school_a)

        res = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertEqual(res.status_code, 200)
        self.assertNotIn("parent_enrollment_guidance", res.json())

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_progress_still_works_when_solomon_unavailable(self):
        client = self._authed_client(self.school_a)

        with patch("onboarding.solomon_services.OnboardingAdapter", side_effect=RuntimeError("down")):
            res = client.get(
                f"/api/v1/onboarding/{self.school_a.id}/progress/",
                {"include_parent_guidance": "1"},
            )

        self.assertEqual(res.status_code, 200)
        self.assertNotIn("parent_enrollment_guidance", res.json())

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_progress_still_works_with_empty_solomon_response(self):
        client = self._authed_client(self.school_a)

        res = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertEqual(res.status_code, 200)
        guidance = res.json().get("parent_enrollment_guidance")
        self.assertTrue(guidance is None or guidance.get("status") == "empty")

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_progress_still_works_with_invalid_solomon_data(self):
        client = self._authed_client(self.school_a)

        with patch("onboarding.solomon_services.OnboardingAdapter.get_context", return_value=object()):
            res = client.get(
                f"/api/v1/onboarding/{self.school_a.id}/progress/",
                {"include_parent_guidance": "1"},
            )

        self.assertEqual(res.status_code, 200)
        self.assertNotIn("parent_enrollment_guidance", res.json())

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_tenant_isolation_remains_enforced(self):
        client = self._authed_client(self.school_a)

        res = client.get(
            f"/api/v1/onboarding/{self.school_b.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertEqual(res.status_code, 403)

    @override_settings(CROWN_SOLOMON_API_ENABLED=True, CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_no_auth_leakage(self):
        client = APIClient()
        client.credentials(HTTP_X_SCHOOL_ID=str(self.school_a.id))

        res = client.get(
            f"/api/v1/onboarding/{self.school_a.id}/progress/",
            {"include_parent_guidance": "1"},
        )

        self.assertIn(res.status_code, (401, 403))
