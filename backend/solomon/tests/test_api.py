"""Read-only SOLOMON API and context resolver tests."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

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
    SolomonTopic,
)
from solomon.services import SolomonContextResolver


User = get_user_model()


@override_settings(CROWN_SOLOMON_API_ENABLED=True, ROOT_URLCONF="solomon.urls")
class SolomonReadOnlyApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="solomon-staff",
            password="password",
            is_staff=True,
        )
        self.user = User.objects.create_user(
            username="solomon-user",
            password="password",
        )

        self.public_category = SolomonCategory.objects.create(
            name="Public Guides",
            slug="public-guides",
            is_public=True,
            sort_order=1,
        )
        self.private_category = SolomonCategory.objects.create(
            name="Private Guides",
            slug="private-guides",
            is_public=False,
            sort_order=2,
        )

        self.public_audience = SolomonAudience.objects.create(
            name="Teachers",
            slug="teachers",
            role_code="teacher",
            is_public=True,
        )
        self.private_audience = SolomonAudience.objects.create(
            name="Directors",
            slug="directors",
            role_code="director",
            is_public=False,
        )

        self.topic = SolomonTopic.objects.create(
            name="Admissions",
            slug="admissions",
        )

        self.global_resource = SolomonResource.objects.create(
            title="Published Welcome Guide",
            slug="published-welcome-guide",
            summary="Visible by default.",
            content="Welcome",
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.AUTHENTICATED,
            scope=SolomonScope.GLOBAL,
            category=self.public_category,
            module="onboarding",
            route_path="/teacher/home",
        )
        self.global_resource.topics.add(self.topic)
        self.global_resource.audiences.add(self.public_audience, self.private_audience)

        self.school_resource = SolomonResource.objects.create(
            title="School Scoped Guide",
            slug="school-scoped-guide",
            summary="Scope-limited guidance.",
            content="Scoped guidance",
            resource_type=SolomonResourceType.ARTICLE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.AUTHENTICATED,
            scope=SolomonScope.SCHOOL,
            category=self.public_category,
            module="onboarding",
            route_path="/teacher/home",
        )
        self.school_resource.audiences.add(self.public_audience)

        self.draft_resource = SolomonResource.objects.create(
            title="Draft Guide",
            slug="draft-guide",
            summary="Hidden until staff access.",
            content="Draft",
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.DRAFT,
            visibility=SolomonVisibility.AUTHENTICATED,
            scope=SolomonScope.GLOBAL,
            category=self.public_category,
            module="onboarding",
            route_path="/teacher/home",
        )

        self.staff_resource = SolomonResource.objects.create(
            title="Staff Only Guide",
            slug="staff-only-guide",
            summary="Visible only to staff/admin.",
            content="Staff only",
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.private_category,
            module="onboarding",
            route_path="/teacher/home",
        )

        self.playbook = SolomonPlaybook.objects.create(
            title="Teacher Welcome Playbook",
            slug="teacher-welcome-playbook",
            summary="How to guide teachers.",
            module="onboarding",
            category=self.public_category,
            visibility=SolomonVisibility.AUTHENTICATED,
            status=SolomonLifecycle.PUBLISHED,
            route_path="/teacher/home",
        )
        self.playbook.audiences.add(self.public_audience, self.private_audience)

        self.draft_playbook = SolomonPlaybook.objects.create(
            title="Draft Playbook",
            slug="draft-playbook",
            summary="Hidden until staff access.",
            module="onboarding",
            category=self.public_category,
            visibility=SolomonVisibility.AUTHENTICATED,
            status=SolomonLifecycle.DRAFT,
            route_path="/teacher/home",
        )

        self.context_rule = SolomonContextRule.objects.create(
            module="onboarding",
            route_path="/teacher/home",
            context_key="teacher-home",
            resource=self.global_resource,
            playbook=self.playbook,
            audience=self.public_audience,
            priority=10,
            is_active=True,
        )
        self.inactive_context_rule = SolomonContextRule.objects.create(
            module="onboarding",
            route_path="/teacher/home",
            context_key="inactive-home",
            resource=self.draft_resource,
            playbook=self.draft_playbook,
            audience=self.private_audience,
            priority=20,
            is_active=False,
        )

    def test_feature_flag_defaults_closed(self):
        with override_settings(CROWN_SOLOMON_API_ENABLED=False, ROOT_URLCONF="solomon.urls"):
            self.client.force_authenticate(user=self.user)
            response = self.client.get("/api/solomon/resources/")

        self.assertEqual(response.status_code, 404)

    def test_read_only_endpoints_return_ok_and_post_is_blocked(self):
        self.client.force_authenticate(user=self.user)

        for path in (
            "/api/solomon/categories/",
            "/api/solomon/topics/",
            "/api/solomon/audiences/",
            "/api/solomon/resources/",
            "/api/solomon/playbooks/",
            "/api/solomon/context/?module=onboarding&route=/teacher/home&audience=teachers&scope=global",
        ):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)

        post_response = self.client.post("/api/solomon/resources/", {})
        self.assertEqual(post_response.status_code, 405)

    def test_category_and_audience_visibility_is_fail_closed(self):
        private_category = SolomonCategory.objects.create(
            name="Hidden",
            slug="hidden",
            is_public=False,
            sort_order=99,
        )
        private_audience = SolomonAudience.objects.create(
            name="Hidden Audience",
            slug="hidden-audience",
            is_public=False,
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/solomon/categories/")
        categories = [item["slug"] for item in response.json()]
        self.assertIn("public-guides", categories)
        self.assertNotIn("hidden", categories)

        response = self.client.get("/api/solomon/audiences/")
        audiences = [item["slug"] for item in response.json()]
        self.assertIn("teachers", audiences)
        self.assertNotIn(private_audience.slug, audiences)

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/categories/")
        categories = [item["slug"] for item in response.json()]
        self.assertIn(private_category.slug, categories)

        response = self.client.get("/api/solomon/audiences/")
        audiences = [item["slug"] for item in response.json()]
        self.assertIn(private_audience.slug, audiences)

    def test_resource_visibility_filters_drafts_and_private_visibility(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/solomon/resources/")
        slugs = [item["slug"] for item in response.json()]
        self.assertIn(self.global_resource.slug, slugs)
        self.assertNotIn(self.draft_resource.slug, slugs)
        self.assertNotIn(self.staff_resource.slug, slugs)

        response = self.client.get("/api/solomon/resources/?scope=school")
        slugs = [item["slug"] for item in response.json()]
        self.assertIn(self.global_resource.slug, slugs)
        self.assertIn(self.school_resource.slug, slugs)

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/resources/")
        slugs = [item["slug"] for item in response.json()]
        self.assertIn(self.global_resource.slug, slugs)
        self.assertIn(self.draft_resource.slug, slugs)
        self.assertIn(self.staff_resource.slug, slugs)

    def test_playbook_visibility_filters_drafts(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/solomon/playbooks/")
        slugs = [item["slug"] for item in response.json()]
        self.assertIn(self.playbook.slug, slugs)
        self.assertNotIn(self.draft_playbook.slug, slugs)

        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/playbooks/")
        slugs = [item["slug"] for item in response.json()]
        self.assertIn(self.playbook.slug, slugs)
        self.assertIn(self.draft_playbook.slug, slugs)

    def test_context_endpoint_exposes_relevant_items_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/solomon/context/?module=onboarding&route=/teacher/home&audience=teachers&scope=school"
        )

        payload = response.json()
        resource_slugs = [item["slug"] for item in payload["resources"]]
        playbook_slugs = [item["slug"] for item in payload["playbooks"]]
        context_keys = [item["context_key"] for item in payload["context_help"]]

        self.assertEqual(payload["module"], "onboarding")
        self.assertEqual(payload["route"], "/teacher/home")
        self.assertEqual(payload["audience"], "teachers")
        self.assertEqual(payload["scope"], "school")
        self.assertIn(self.global_resource.slug, resource_slugs)
        self.assertIn(self.global_resource.slug, [item["slug"] for item in payload["guides"]])
        self.assertIn(self.playbook.slug, playbook_slugs)
        self.assertIn(self.context_rule.context_key, context_keys)
        self.assertNotIn(self.inactive_context_rule.context_key, context_keys)


@override_settings(CROWN_SOLOMON_API_ENABLED=True, ROOT_URLCONF="solomon.urls")
class SolomonContextResolverTests(TestCase):
    def test_invalid_scope_fails_closed(self):
        user = User.objects.create_user(username="resolver-user", password="password")
        request = type("Request", (), {"user": user})()
        resolver = SolomonContextResolver(
            request=request,
            module="onboarding",
            route="/teacher/home",
            audience="teachers",
            scope="not-a-real-scope",
        )

        payload = resolver.resolve()
        self.assertEqual(payload["resources"], [])
        self.assertEqual(payload["playbooks"], [])
        self.assertEqual(payload["context_help"], [])