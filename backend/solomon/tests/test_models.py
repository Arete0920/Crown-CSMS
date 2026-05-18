"""Tests for SOLOMON Phase 2 core knowledge models."""

from django.db import IntegrityError
from django.test import TestCase

from solomon.models import (
    SolomonAudience,
    SolomonCategory,
    SolomonContextRule,
    SolomonLifecycle,
    SolomonPlaybook,
    SolomonResource,
    SolomonResourceType,
    SolomonResourceVersion,
    SolomonScope,
    SolomonTopic,
    SolomonVisibility,
)


class SolomonPhase2ModelTests(TestCase):
    def test_category_creation_and_str(self):
        category = SolomonCategory.objects.create(name="Admissions", slug="admissions")
        self.assertEqual(str(category), "Admissions")

    def test_category_slug_uniqueness(self):
        SolomonCategory.objects.create(name="Admissions", slug="admissions")
        with self.assertRaises(IntegrityError):
            SolomonCategory.objects.create(name="Admissions Duplicate", slug="admissions")

    def test_topic_creation_and_str(self):
        topic = SolomonTopic.objects.create(name="Enrollment", slug="enrollment")
        self.assertEqual(str(topic), "Enrollment")

    def test_audience_creation_and_str(self):
        audience = SolomonAudience.objects.create(
            name="Teacher",
            slug="teacher",
            role_code="teacher",
        )
        self.assertEqual(str(audience), "Teacher")

    def test_resource_creation_and_defaults(self):
        category = SolomonCategory.objects.create(name="Getting Started", slug="getting-started")
        resource = SolomonResource.objects.create(
            title="Welcome Guide",
            slug="welcome-guide",
            category=category,
            content="Welcome content",
        )

        self.assertEqual(str(resource), "SolomonResource(welcome-guide)")
        self.assertEqual(resource.resource_type, SolomonResourceType.ARTICLE)
        self.assertEqual(resource.status, SolomonLifecycle.DRAFT)
        self.assertEqual(resource.visibility, SolomonVisibility.AUTHENTICATED)
        self.assertEqual(resource.scope, SolomonScope.SCHOOL)

    def test_resource_lifecycle_values(self):
        resource = SolomonResource.objects.create(
            title="Policy",
            slug="policy",
            status=SolomonLifecycle.APPROVED,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
        )

        self.assertEqual(resource.status, "approved")
        self.assertEqual(resource.visibility, "staff")
        self.assertEqual(resource.scope, "global")

    def test_resource_topic_and_audience_assignment(self):
        topic = SolomonTopic.objects.create(name="Payments", slug="payments")
        audience = SolomonAudience.objects.create(name="Parent", slug="parent")
        resource = SolomonResource.objects.create(title="Payment Guide", slug="payment-guide")

        resource.topics.add(topic)
        resource.audiences.add(audience)

        self.assertEqual(resource.topics.count(), 1)
        self.assertEqual(resource.audiences.count(), 1)
        self.assertEqual(resource.topics.first(), topic)
        self.assertEqual(resource.audiences.first(), audience)

    def test_resource_version_creation(self):
        resource = SolomonResource.objects.create(title="Handbook", slug="handbook")
        version = SolomonResourceVersion.objects.create(
            resource=resource,
            version="1.0",
            title="Handbook",
            content="Versioned content",
            change_note="Initial version",
        )

        self.assertEqual(str(version), "SolomonResourceVersion(handbook, 1.0)")
        self.assertEqual(resource.versions.count(), 1)

    def test_playbook_checklist_default_list(self):
        playbook = SolomonPlaybook.objects.create(title="Billing Playbook", slug="billing-playbook")
        self.assertEqual(str(playbook), "SolomonPlaybook(billing-playbook)")
        self.assertEqual(playbook.checklist, [])

    def test_context_rule_ordering_and_str(self):
        audience = SolomonAudience.objects.create(name="Staff", slug="staff")
        resource = SolomonResource.objects.create(title="Staff Guide", slug="staff-guide")
        playbook = SolomonPlaybook.objects.create(title="Staff Playbook", slug="staff-playbook")

        second = SolomonContextRule.objects.create(
            module="billing",
            route_path="/billing",
            context_key="second",
            resource=resource,
            playbook=playbook,
            audience=audience,
            priority=20,
        )
        first = SolomonContextRule.objects.create(
            module="billing",
            route_path="/billing",
            context_key="first",
            priority=10,
        )

        ordered = list(SolomonContextRule.objects.filter(module="billing"))
        self.assertEqual(ordered, [first, second])
        self.assertEqual(str(first), "SolomonContextRule(billing, /billing, first)")
