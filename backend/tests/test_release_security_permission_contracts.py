"""
Release security permission contracts for priorities 036-039.
"""

import uuid

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _user_for_school(school, *, is_staff=False, prefix="release-security"):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"{prefix}-{token}",
        email=f"{prefix}-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=is_staff,
    )


class TestReleaseSecurityPermissionContracts:
    def setup_method(self):
        self.school_a = School.objects.create(name="Release Security School A")
        self.school_b = School.objects.create(name="Release Security School B")
        self.user_a = _user_for_school(self.school_a, prefix="release-a")
        self.client = APIClient()

    @override_settings(TENANT_HEADER_REQUIRED=True)
    @pytest.mark.parametrize(
        "method,path,payload",
        [
            ("post", "/api/v1/academics/courses/", {}),
            ("post", "/api/v1/gradebook/sections/", {}),
            ("post", "/api/v1/billing/runs/", {}),
        ],
    )
    def test_036_tenant_header_required_on_write_surfaces(self, method, path, payload):
        self.client.force_authenticate(user=self.user_a)
        response = getattr(self.client, method)(path, payload, format="json")
        assert response.status_code in (400, 403, 405), (
            f"Expected fail-closed status for missing X-School-Id on {path}, got {response.status_code}"
        )
        if response.status_code == 400:
            assert b"X-School-Id" in response.content

    def test_037_cross_tenant_read_negative_gradebook(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/gradebook/sections/",
            HTTP_X_SCHOOL_ID=str(self.school_b.id),
        )
        assert response.status_code == 404

    def test_037_cross_tenant_write_negative_admissions(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.post(
            "/api/admissions/enroll/",
            {},
            format="json",
            HTTP_X_SCHOOL_ID=str(self.school_b.id),
        )
        assert response.status_code == 404

    def test_038_object_level_permission_escalation_blocked_exports(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/reports/export/",
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )
        assert response.status_code == 403

    def test_038_object_level_permission_escalation_blocked_billing_runs(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/billing/runs/",
            HTTP_X_SCHOOL_ID=str(self.school_a.id),
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/reports/export/",
            "/api/v1/billing/runs/",
        ],
    )
    def test_039_role_permission_matrix_anonymous_denied(self, path):
        response = self.client.get(path, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        assert response.status_code in (401, 403)

    @pytest.mark.parametrize(
        "path",
        [
            "/api/v1/reports/export/",
            "/api/v1/billing/runs/",
        ],
    )
    def test_039_role_permission_matrix_non_privileged_denied(self, path):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(path, HTTP_X_SCHOOL_ID=str(self.school_a.id))
        assert response.status_code == 403
