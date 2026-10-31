import json

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from core.models import School
from crown_api.tenant import TenantContext
from subscriptions.models import SchoolModule
from subscriptions.views import (
    activate_module,
    deactivate_module,
    list_school_modules,
    start_trial,
)

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


def _json(response):
    return json.loads(response.content.decode("utf-8"))


class AdminModuleCanonicalTenantTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.school = School.objects.create(name="Canonical Modules School")
        self.staff = User.objects.create_superuser(
            username="canonical-module-admin",
            email="canonical-module-admin@example.com",
            password="test-password",
        )

    def _request(self, method, path, payload=None, with_context=True):
        request_method = getattr(self.factory, method)
        if method.lower() == "get":
            request = request_method(path)
        else:
            request = request_method(
                path,
                data=json.dumps(payload or {}),
                content_type="application/json",
            )
        request.user = self.staff
        if with_context:
            request.crown_tenant = _canonical_context(self.school)
        self.assertFalse(hasattr(request, "school_id"))
        return request

    def test_list_modules_uses_canonical_context_without_legacy_alias(self):
        SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
        )
        response = list_school_modules(self._request("get", "/api/v1/admin/modules/"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(_json(response)["school_id"], str(self.school.id))

    def test_activate_module_uses_canonical_context_without_legacy_alias(self):
        response = activate_module(
            self._request(
                "post",
                "/api/v1/admin/modules/activate/",
                {"module_key": "financial_aid", "months": 12},
            )
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            SchoolModule.objects.filter(
                school=self.school,
                module_key="financial_aid",
                status="active",
            ).exists()
        )

    def test_deactivate_module_uses_canonical_context_without_legacy_alias(self):
        SchoolModule.objects.create(
            school=self.school,
            module_key="financial_aid",
            status="active",
        )
        response = deactivate_module(
            self._request(
                "post",
                "/api/v1/admin/modules/deactivate/",
                {"module_key": "financial_aid"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            SchoolModule.objects.get(
                school=self.school,
                module_key="financial_aid",
            ).status,
            "inactive",
        )

    def test_start_trial_uses_canonical_context_without_legacy_alias(self):
        response = start_trial(
            self._request(
                "post",
                "/api/v1/admin/modules/trial/",
                {"module_key": "financial_aid", "days": 30},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            SchoolModule.objects.get(
                school=self.school,
                module_key="financial_aid",
            ).status,
            "trial",
        )

    def test_missing_canonical_context_fails_closed(self):
        response = list_school_modules(
            self._request(
                "get",
                "/api/v1/admin/modules/",
                with_context=False,
            )
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(_json(response)["code"], "TENANT_REQUIRED")

    def test_school_staff_is_not_module_operator(self):
        staff = User.objects.create_user(
            username="school-only-module-staff",
            email="school-only@example.invalid",
            password="test",
            is_staff=True,
            school=self.school,
        )
        request = self._request("post", "/api/v1/admin/modules/activate/", {
            "module_key": "before_care", "months": 12,
        })
        request.user = staff
        response = activate_module(request)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SchoolModule.objects.filter(school=self.school, module_key="before_care").exists())

    def test_unscoped_staff_without_superuser_cannot_start_trial(self):
        staff = User.objects.create_user(
            username="unscoped-staff",
            email="staff-only@example.invalid",
            password="test",
            is_staff=True,
        )
        request = self._request("post", "/api/v1/admin/modules/trial/", {
            "module_key": "after_care",
        })
        request.user = staff
        response = start_trial(request)
        self.assertEqual(response.status_code, 403)
        self.assertFalse(SchoolModule.objects.filter(school=self.school, module_key="after_care").exists())

    def test_trial_accepts_new_care_key_only_for_platform_operator(self):
        from platform_ops.models import AuditEvent
        response = start_trial(self._request("post", "/api/v1/admin/modules/trial/", {
            "module_key": "before_care", "days": 7,
        }))
        self.assertEqual(response.status_code, 200)
        mod = SchoolModule.objects.get(school=self.school, module_key="before_care")
        self.assertTrue(mod.is_trial)
        self.assertFalse(SchoolModule.objects.filter(school=self.school, module_key="after_care").exists())
        self.assertEqual(AuditEvent.objects.get(action="subscription.module_trial_started").actor_user_id, self.staff.id)

    def test_care_activation_rejects_unapproved_price_and_invalid_months(self):
        from platform_ops.models import AuditEvent
        for body in (
            {"module_key": "before_care", "price_paid": 10, "months": 12},
            {"module_key": "before_care", "months": 0},
            {"module_key": "before_care", "months": True},
            {"module_key": "before_care", "months": -1},
        ):
            response = activate_module(self._request("post", "/api/v1/admin/modules/activate/", body))
            self.assertEqual(response.status_code, 400)
        self.assertFalse(SchoolModule.objects.filter(school=self.school, module_key="before_care").exists())
        self.assertEqual(AuditEvent.objects.count(), 0)

    def test_invalid_trial_key_does_not_create_entitlement(self):
        for body in (
            {"module_key": "not-a-module", "days": 7},
            {"module_key": "after_care", "days": 0},
            {"module_key": "after_care", "days": True},
        ):
            response = start_trial(self._request("post", "/api/v1/admin/modules/trial/", body))
            self.assertEqual(response.status_code, 400)
        self.assertFalse(SchoolModule.objects.filter(school=self.school).exists())

    def test_care_entitlement_audit_failure_rolls_back_activation(self):
        from unittest.mock import patch
        with patch("subscriptions.views.AuditEvent.objects.create", side_effect=RuntimeError("audit offline")):
            with self.assertRaises(RuntimeError):
                activate_module(self._request("post", "/api/v1/admin/modules/activate/", {
                    "module_key": "before_care", "months": 12,
                }))
        self.assertFalse(SchoolModule.objects.filter(school=self.school, module_key="before_care").exists())

