"""Tests for Crown module tier gates and lifecycle."""
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.test import RequestFactory, TestCase
from django.utils import timezone

from core.models import School
from crown_api.tenant import TenantContext
from subscriptions.gates import get_school_modules, require_module, school_has_module
from subscriptions.models import SchoolModule

User = get_user_model()


def _canonical_context(school):
    return TenantContext(
        school_id=school.id,
        school=school,
        source="test",
        header_present=False,
        principal_school_id=school.id,
        override_requested=False,
        override_authorized=False,
        actor_type="user",
    )


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
        self.assertFalse(school_has_module(self.school.id, "financial_aid"))

    def test_require_module_decorator_blocks_without_canonical_context(self):
        request = self.factory.get("/test/")

        @require_module("financial_aid")
        def fake_view(_request):
            return JsonResponse({"ok": True})

        response = fake_view(request)
        self.assertEqual(response.status_code, 400)

    def test_require_module_blocks_without_entitlement_from_canonical_context(self):
        request = self.factory.get("/test/")
        request.crown_tenant = _canonical_context(self.school)
        self.assertFalse(hasattr(request, "school_id"))

        @require_module("financial_aid")
        def fake_view(_request):
            return JsonResponse({"ok": True})

        response = fake_view(request)
        self.assertEqual(response.status_code, 403)

    def test_require_module_passes_from_canonical_context_without_legacy_alias(self):
        SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
            expiry_date=timezone.now() + timezone.timedelta(days=30),
        )
        request = self.factory.get("/test/")
        request.crown_tenant = _canonical_context(self.school)
        self.assertFalse(hasattr(request, "school_id"))

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


class StandaloneCareEntitlementTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Standalone Care Tenant")

    def test_both_independent_keys_default_disabled(self):
        keys = {k for k, _ in SchoolModule.MODULE_CHOICES}
        self.assertTrue({"before_care", "after_care", "little_lambs"}.issubset(keys))
        self.assertFalse(school_has_module(self.school.id, "before_care"))
        self.assertFalse(school_has_module(self.school.id, "after_care"))
        self.assertFalse(school_has_module(self.school.id, "little_lambs"))

    def test_am_only_never_unlocks_pm_or_diadem(self):
        SchoolModule.objects.create(
            school=self.school, module_key="before_care", status="active",
            expiry_date=timezone.now() + timezone.timedelta(days=30),
        )
        self.assertTrue(school_has_module(self.school.id, "before_care"))
        self.assertFalse(school_has_module(self.school.id, "after_care"))
        self.assertFalse(school_has_module(self.school.id, "little_lambs"))

    def test_care_trial_expiry_suspension_and_missing_expiry_fail_closed(self):
        for key in ("before_care", "after_care"):
            module = SchoolModule.objects.create(school=self.school, module_key=key, status="trial")
            self.assertFalse(school_has_module(self.school.id, key))
            module.expiry_date = timezone.now() + timezone.timedelta(days=7)
            module.save(update_fields=["expiry_date"])
            self.assertTrue(school_has_module(self.school.id, key))
            module.status = "suspended"
            module.save(update_fields=["status"])
            self.assertFalse(school_has_module(self.school.id, key))
            module.status = "active"
            module.expiry_date = timezone.now() - timezone.timedelta(seconds=1)
            module.save(update_fields=["status", "expiry_date"])
            self.assertFalse(school_has_module(self.school.id, key))

    def test_inactive_care_tenant_not_entitled(self):
        module = SchoolModule.objects.create(
            school=self.school, module_key="after_care", status="active",
            expiry_date=timezone.now() + timezone.timedelta(days=30),
        )
        assert module.is_active
        self.school.is_active = False
        self.school.save(update_fields=["is_active"])
        self.assertFalse(school_has_module(self.school.id, "after_care"))

