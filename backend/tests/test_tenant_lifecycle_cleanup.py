import pytest
from django.http import JsonResponse
from django.test import TestCase, override_settings
from django.urls import path

from core.models import School
from core.tenant_models import get_current_school, clear_current_school

# --- Test views ---
def ok_view(request):
    return JsonResponse({"ok": True})

def boom_view(request):
    raise RuntimeError("boom")

# --- Test URLConf ---
urlpatterns = [
    path("_test/ok/", ok_view),
    path("_test/boom/", boom_view),
]

@override_settings(ROOT_URLCONF=__name__)
class TestTenantLifecycleCleanup(TestCase):
    def setUp(self):
        clear_current_school()
        self.school = School.objects.create(name="Tenant A")

    def tearDown(self):
        clear_current_school()

    def test_context_cleared_after_ok_request(self):
        # Make request with tenant header, ensure request processing clears afterwards
        resp = self.client.get("/_test/ok/", HTTP_X_SCHOOL_ID=str(self.school.id))
        assert resp.status_code == 200
        assert get_current_school() is None

    def test_context_cleared_after_exception_request(self):
        # Exception in view should still clear context via middleware finally
        # Django test client catches exceptions and returns 500 by default
        resp = self.client.get("/_test/boom/", HTTP_X_SCHOOL_ID=str(self.school.id))
        assert resp.status_code == 500
        assert get_current_school() is None
