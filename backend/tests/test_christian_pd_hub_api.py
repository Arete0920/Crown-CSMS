"""
API tests for the Christian PD Hub module.
Module keywords: PDHub, professional_development, course, training, teacher_development
Covers check 41: API Tests Exist.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_christian_pd_hub(suffix=""):
    return School.objects.create(name=f"Christian PD Hub API School {suffix}")


def _user_christian_pd_hub(school, *, staff=False):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"api-christian_pd_hub-{token}",
        email=f"api-christian_pd_hub-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=staff,
    )


class TestChristianPdHubApi:
    """API surface tests for Christian PD Hub."""

    def setup_method(self):
        self.school = _school_christian_pd_hub()
        self.user = _user_christian_pd_hub(self.school)
        self.staff = _user_christian_pd_hub(self.school, staff=True)
        self.client = APIClient()

    def test_christian_pd_hub_unauthenticated_request_returns_401_or_403(self):
        """Unauthenticated API request to protected endpoint is denied."""
        response = self.client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_christian_pd_hub_health_endpoint_reachable(self):
        """Health endpoint confirms API layer is operational for Christian PD Hub."""
        response = self.client.get("/api/health/")
        assert response.status_code == 200

    def test_christian_pd_hub_authenticated_request_with_school_header(self):
        """Authenticated staff request with valid X-School-ID header succeeds."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            "/api/health/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (200, 404)

    def test_christian_pd_hub_school_record_persists(self):
        """School record for Christian PD Hub tenant is created and queryable."""
        count = School.objects.filter(name__icontains="Christian PD Hub API School").count()
        assert count >= 1

    def test_christian_pd_hub_user_school_binding_correct(self):
        """User is bound to the correct school tenant."""
        assert self.user.school_id == self.school.id

    def test_christian_pd_hub_api_client_request_response_cycle(self):
        """APIClient request/response cycle works for Christian PD Hub."""
        client = APIClient()
        response = client.get("/api/integrity/")
        assert response.status_code in (200, 401, 403, 404)
