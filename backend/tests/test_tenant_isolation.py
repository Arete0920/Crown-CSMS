import uuid

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School


pytestmark = pytest.mark.django_db
User = get_user_model()


def _user_for_school(school: School, *, is_staff: bool = False, username_prefix: str = "tenant"):
    token = uuid.uuid4()
    return User.objects.create_user(
        username=f"{username_prefix}-{token}",
        email=f"{username_prefix}-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=is_staff,
    )


class TestTenantIsolation:
    def setup_method(self):
        self.school_a = School.objects.create(name="Tenant A School")
        self.school_b = School.objects.create(name="Tenant B School")
        self.user_a = _user_for_school(self.school_a, username_prefix="tenant-a")
        self.staff_a = _user_for_school(self.school_a, is_staff=True, username_prefix="tenant-staff")
        token = uuid.uuid4()
        self.user_without_school = User.objects.create_user(
            username=f"tenant-none-{token}",
            email=f"tenant-none-{token}@example.com",
            password="Passw0rd!",
        )
        self.client = APIClient()

    def test_gradebook_sections_missing_header_returns_400(self):
        self.client.force_authenticate(user=self.user_without_school)
        response = self.client.get("/api/v1/gradebook/sections/")
        assert response.status_code == 400

    def test_gradebook_sections_cross_tenant_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/v1/gradebook/sections/", HTTP_X_SCHOOL_ID=str(self.school_b.id))
        assert response.status_code == 404

    def test_billing_runs_cross_tenant_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/v1/billing/runs/", HTTP_X_SCHOOL_ID=str(self.school_b.id))
        assert response.status_code == 404

    def test_admissions_applications_cross_tenant_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/admissions/applications/", HTTP_X_SCHOOL_ID=str(self.school_b.id))
        assert response.status_code == 404

    def test_admissions_enroll_cross_tenant_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post("/api/admissions/enroll/", {}, format="json", HTTP_X_SCHOOL_ID=str(self.school_b.id))
        assert response.status_code == 404

    def test_staff_same_tenant_can_reach_gradebook_surface(self):
        self.client.force_authenticate(user=self.staff_a)
        response = self.client.get("/api/v1/gradebook/sections/", HTTP_X_SCHOOL_ID=str(self.school_a.id))
        assert response.status_code == 200

    def test_unauthenticated_request_is_denied(self):
        response = self.client.get("/api/v1/billing/runs/", HTTP_X_SCHOOL_ID=str(self.school_a.id))
        assert response.status_code in (401, 403)