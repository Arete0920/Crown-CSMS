"""Tests for SOLOMON internal context adapters (Phase 3B-A)."""

from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from solomon.adapters import (
    AcademicsAdapter,
    FinanceAdapter,
    OnboardingAdapter,
    SolomonContextPayload,
    SolomonContextRequest,
    SpiritualLifeAdapter,
)
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


class SolomonAdapterBaseTests(TestCase):
    """Adapter base contract and fail-closed semantics."""

    def setUp(self):
        self.category = SolomonCategory.objects.create(name="Enrollment", slug="enrollment")
        self.public_audience = SolomonAudience.objects.create(
            name="Parent",
            slug="parent",
            role_code="parent",
            is_public=True,
        )

        self.resource = SolomonResource.objects.create(
            title="How to Enroll",
            slug="how-to-enroll",
            category=self.category,
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.SCHOOL,
            module="onboarding",
            route_path="/students/enrollment",
        )
        self.resource.audiences.add(self.public_audience)

        self.playbook = SolomonPlaybook.objects.create(
            title="Enrollment Process",
            slug="enrollment-process",
            summary="Step-by-step enrollment",
            module="onboarding",
            route_path="/students/enrollment",
            visibility=SolomonVisibility.PUBLIC,
            status=SolomonLifecycle.PUBLISHED,
            category=self.category,
        )
        self.playbook.audiences.add(self.public_audience)

        self.context_rule = SolomonContextRule.objects.create(
            module="onboarding",
            route_path="/students/enrollment",
            context_key="welcome-parent",
            audience=self.public_audience,
            resource=self.resource,
            playbook=self.playbook,
            is_active=True,
        )

        self.user = User.objects.create_user(
            username="adapter_base_user",
            email="adapter_base@example.com",
            password="pass123",
        )
        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.school_id = None

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=False)
    def test_adapter_returns_disabled_payload_when_flag_is_false(self):
        adapter = OnboardingAdapter()
        req = SolomonContextRequest(
            module="onboarding",
            route="/students/enrollment",
            audience="parent",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "disabled")
        self.assertEqual(payload.resources, [])
        self.assertEqual(payload.playbooks, [])
        self.assertEqual(payload.context_rules, [])

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_adapter_returns_empty_payload_when_no_context_found(self):
        adapter = FinanceAdapter()
        req = SolomonContextRequest(
            module="finance",
            route="/billing/nonexistent",
            audience="student",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "empty")
        self.assertEqual(payload.resources, [])
        self.assertEqual(payload.playbooks, [])
        self.assertEqual(payload.context_rules, [])

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_adapter_returns_error_payload_on_unhandled_exception(self):
        adapter = OnboardingAdapter()
        req = SolomonContextRequest(
            module="onboarding",
            route="/students/enrollment",
            audience="parent",
            request=self.mock_request,
        )

        with patch.object(adapter, "_resolve_context", side_effect=RuntimeError("boom")):
            payload = adapter.get_context(req)

        self.assertEqual(payload.status, "error")
        self.assertEqual(payload.metadata["error_type"], "RuntimeError")

    def test_context_payload_to_dict(self):
        payload = SolomonContextPayload(
            status="resolved",
            resources=[{"id": 1, "title": "Test"}],
            playbooks=[{"id": 2, "title": "Workflow"}],
            context_rules=[{"id": 3, "context_key": "help"}],
            metadata={"module": "onboarding"},
        )

        data = payload.to_dict()

        self.assertEqual(data["status"], "resolved")
        self.assertEqual(len(data["resources"]), 1)
        self.assertEqual(len(data["playbooks"]), 1)
        self.assertEqual(len(data["context_rules"]), 1)
        self.assertEqual(data["metadata"]["module"], "onboarding")


class OnboardingAdapterTests(TestCase):
    def setUp(self):
        self.category = SolomonCategory.objects.create(name="Enrollment", slug="enrollment-ob")
        self.parent_audience = SolomonAudience.objects.create(
            name="Parent",
            slug="parent-ob",
            role_code="parent",
            is_public=True,
        )

        self.resource = SolomonResource.objects.create(
            title="Parent Enrollment Guide",
            slug="parent-enrollment-guide",
            category=self.category,
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.SCHOOL,
            module="onboarding",
            route_path="/students/enrollment",
        )
        self.resource.audiences.add(self.parent_audience)

        self.playbook = SolomonPlaybook.objects.create(
            title="Parent Onboarding",
            slug="parent-onboarding",
            summary="Getting started as a parent",
            module="onboarding",
            route_path="/students/enrollment",
            visibility=SolomonVisibility.PUBLIC,
            status=SolomonLifecycle.PUBLISHED,
            category=self.category,
        )
        self.playbook.audiences.add(self.parent_audience)

        SolomonContextRule.objects.create(
            module="onboarding",
            route_path="/students/enrollment",
            context_key="parent-checklist",
            audience=self.parent_audience,
            resource=self.resource,
            playbook=self.playbook,
            is_active=True,
        )

        self.user = User.objects.create_user(
            username="adapter_onboarding_user",
            email="adapter_onboarding@example.com",
            password="pass123",
        )
        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.school_id = None

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_onboarding_adapter_resolves_parent_context(self):
        adapter = OnboardingAdapter()
        req = SolomonContextRequest(
            module="onboarding",
            route="/students/enrollment",
            audience="parent",
            scope="school",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "resolved")
        self.assertGreaterEqual(len(payload.context_rules), 1)
        self.assertEqual(payload.metadata["module"], "onboarding")
        self.assertEqual(payload.metadata["route"], "/students/enrollment")

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_onboarding_adapter_rejects_non_onboarding_module(self):
        adapter = OnboardingAdapter()
        req = SolomonContextRequest(
            module="finance",
            route="/students/enrollment",
            audience="parent",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "empty")

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_onboarding_adapter_deterministic_output(self):
        adapter = OnboardingAdapter()
        req = SolomonContextRequest(
            module="onboarding",
            route="/students/enrollment",
            audience="parent",
            scope="school",
            request=self.mock_request,
        )

        payload1 = adapter.get_context(req).to_dict()
        payload2 = adapter.get_context(req).to_dict()

        self.assertEqual(payload1, payload2)


class FinanceAdapterTests(TestCase):
    def setUp(self):
        self.category = SolomonCategory.objects.create(name="Financial Aid", slug="financial-aid")
        self.student_audience = SolomonAudience.objects.create(
            name="Student",
            slug="student-fin",
            role_code="student",
            is_public=True,
        )

        self.resource = SolomonResource.objects.create(
            title="Financial Aid Application Guide",
            slug="financial-aid-application-guide",
            category=self.category,
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.SCHOOL,
            module="finance",
            route_path="/financial-aid/application",
        )
        self.resource.audiences.add(self.student_audience)

        SolomonContextRule.objects.create(
            module="finance",
            route_path="/financial-aid/application",
            context_key="fafsa-first",
            audience=self.student_audience,
            resource=self.resource,
            is_active=True,
        )

        self.user = User.objects.create_user(
            username="adapter_finance_user",
            email="adapter_finance@example.com",
            password="pass123",
        )
        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.school_id = None

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_finance_adapter_resolves_student_context(self):
        adapter = FinanceAdapter()
        req = SolomonContextRequest(
            module="finance",
            route="/financial-aid/application",
            audience="student",
            scope="school",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "resolved")
        self.assertGreaterEqual(len(payload.context_rules), 1)

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=False)
    def test_finance_adapter_disabled_flag(self):
        adapter = FinanceAdapter()
        req = SolomonContextRequest(
            module="finance",
            route="/financial-aid/application",
            audience="student",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "disabled")


class AcademicsAdapterTests(TestCase):
    def setUp(self):
        self.category = SolomonCategory.objects.create(name="Courses", slug="courses")
        self.student_audience = SolomonAudience.objects.create(
            name="Student",
            slug="student-ac",
            role_code="student",
            is_public=True,
        )

        self.resource = SolomonResource.objects.create(
            title="Course Registration Help",
            slug="course-registration-help",
            category=self.category,
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.SCHOOL,
            module="academics",
            route_path="/courses/enrollment",
        )
        self.resource.audiences.add(self.student_audience)

        SolomonContextRule.objects.create(
            module="academics",
            route_path="/courses/enrollment",
            context_key="registration-period",
            audience=self.student_audience,
            resource=self.resource,
            is_active=True,
        )

        self.user = User.objects.create_user(
            username="adapter_academics_user",
            email="adapter_academics@example.com",
            password="pass123",
        )
        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.school_id = None

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_academics_adapter_resolves_student_context(self):
        adapter = AcademicsAdapter()
        req = SolomonContextRequest(
            module="academics",
            route="/courses/enrollment",
            audience="student",
            scope="school",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "resolved")


class SpiritualLifeAdapterTests(TestCase):
    def setUp(self):
        self.category = SolomonCategory.objects.create(name="Community", slug="community")
        self.student_audience = SolomonAudience.objects.create(
            name="Student",
            slug="student-sp",
            role_code="student",
            is_public=True,
        )

        self.resource = SolomonResource.objects.create(
            title="Chapel Schedule",
            slug="chapel-schedule",
            category=self.category,
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.SCHOOL,
            module="spiritual_life",
            route_path="/chapel/event",
        )
        self.resource.audiences.add(self.student_audience)

        SolomonContextRule.objects.create(
            module="spiritual_life",
            route_path="/chapel/event",
            context_key="weekly-chapel",
            audience=self.student_audience,
            resource=self.resource,
            is_active=True,
        )

        self.user = User.objects.create_user(
            username="adapter_spirit_user",
            email="adapter_spirit@example.com",
            password="pass123",
        )
        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.school_id = None

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_spiritual_life_adapter_resolves_student_context(self):
        adapter = SpiritualLifeAdapter()
        req = SolomonContextRequest(
            module="spiritual_life",
            route="/chapel/event",
            audience="student",
            scope="school",
            request=self.mock_request,
        )

        payload = adapter.get_context(req)

        self.assertEqual(payload.status, "resolved")


class AdapterFailClosedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="adapter_failclosed_user",
            email="adapter_failclosed@example.com",
            password="pass123",
        )
        self.mock_request = Mock()
        self.mock_request.user = self.user
        self.mock_request.school_id = None

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=False)
    def test_all_adapters_respect_disabled_flag(self):
        adapters = [
            OnboardingAdapter(),
            FinanceAdapter(),
            AcademicsAdapter(),
            SpiritualLifeAdapter(),
        ]

        for adapter in adapters:
            req = SolomonContextRequest(
                module="onboarding",
                route="/test",
                request=self.mock_request,
            )
            payload = adapter.get_context(req)
            self.assertEqual(payload.status, "disabled")

    @override_settings(CROWN_SOLOMON_CONTEXT_ENABLED=True)
    def test_adapters_never_raise_exceptions(self):
        adapters = [
            OnboardingAdapter(),
            FinanceAdapter(),
            AcademicsAdapter(),
            SpiritualLifeAdapter(),
        ]

        req = SolomonContextRequest(
            module="nonexistent",
            route="/nonexistent",
            request=self.mock_request,
        )

        for adapter in adapters:
            payload = adapter.get_context(req)
            self.assertIn(payload.status, ["disabled", "empty", "error", "resolved"])
