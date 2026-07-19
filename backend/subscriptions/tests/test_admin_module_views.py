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
        self.staff = User.objects.create_user(
            username="canonical-module-admin",
            email="canonical-module-admin@example.com",
            password="test-password",
            is_staff=True,
            school=self.school,
        )

    def _request(self, method, path, payload=None, with_context=True):
        request = getattr(self.factory, method)(
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
