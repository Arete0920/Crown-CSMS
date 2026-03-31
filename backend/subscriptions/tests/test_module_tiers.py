"""Tests for Crown module tier gates and lifecycle."""

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from core.models import School
from subscriptions.gates import get_school_modules, require_module, school_has_module
from subscriptions.models import SchoolModule

User = get_user_model()


class TestSchoolModuleModel(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Heritage")
        self.admin = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="testpass123",
            is_staff=True,
        )

    def test_is_active_returns_true_for_active_status(self):
        mod = SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
            expiry_date=timezone.now() + timezone.timedelta(days=365),
        )
        self.assertTrue(mod.is_active)

    def test_is_active_returns_false_when_expired(self):
        mod = SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
            expiry_date=timezone.now() - timezone.timedelta(days=1),
        )
        self.assertFalse(mod.is_active)

    def test_is_trial_returns_true_for_trial_status(self):
        mod = SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="trial",
            expiry_date=timezone.now() + timezone.timedelta(days=30),
        )
        self.assertTrue(mod.is_trial)


class TestModuleGate(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Crown Academy")
        self.factory = RequestFactory()

    def test_returns_false_for_nonexistent_module(self):
        result = school_has_module(self.school.id, "financial_aid")
        self.assertFalse(result)

    def test_require_module_decorator_blocks_without_school_context(self):
        request = self.factory.get("/test/")

        @require_module("financial_aid")
        def fake_view(_request):
            return JsonResponse({"ok": True})

        response = fake_view(request)
        self.assertEqual(response.status_code, 400)

    def test_require_module_decorator_blocks_without_entitlement(self):
        request = self.factory.get("/test/")
        request.school_id = self.school.id

        @require_module("financial_aid")
        def fake_view(_request):
            return JsonResponse({"ok": True})

        response = fake_view(request)
        self.assertEqual(response.status_code, 403)

    def test_require_module_passes_with_entitlement(self):
        SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
            expiry_date=timezone.now() + timezone.timedelta(days=30),
        )

        request = self.factory.get("/test/")
        request.school_id = self.school.id

        @require_module("financial_aid")
        def fake_view(_request):
            return JsonResponse({"ok": True})

        response = fake_view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_school_modules_returns_all_keys_and_defaults_to_inactive(self):
        result = get_school_modules(self.school.id)
        all_keys = [k for k, _ in SchoolModule.MODULE_CHOICES]
        for key in all_keys:
            self.assertIn(key, result)
            self.assertEqual(result[key], "inactive")

    def test_get_school_modules_marks_active_and_trial(self):
        SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
            expiry_date=timezone.now() + timezone.timedelta(days=15),
        )
        SchoolModule.objects.create(
            school=self.school,
            module_key="gradebook_pro",
            status="trial",
            expiry_date=timezone.now() + timezone.timedelta(days=5),
        )

        result = get_school_modules(self.school.id)
        self.assertEqual(result["financial_aid"], "active")
        self.assertEqual(result["gradebook_pro"], "trial")
