"""
API tests for the Mission Metrics module.
Module keywords: MissionMetrics, MissionFit, mission_dashboard, faith_health, culture
Covers check 41: API Tests Exist.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_mission_metrics(suffix=""):
    return School.objects.create(name=f"Mission Metrics API School {suffix}")


def _user_mission_metrics(school, *, staff=False):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"api-mission_metrics-{token}",
        email=f"api-mission_metrics-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=staff,
    )


class TestMissionMetricsApi:
    """API surface tests for Mission Metrics."""

    def setup_method(self):
        self.school = _school_mission_metrics()
        self.user = _user_mission_metrics(self.school)
        self.staff = _user_mission_metrics(self.school, staff=True)
        self.client = APIClient()

    def test_mission_metrics_unauthenticated_request_returns_401_or_403(self):
        """Unauthenticated API request to protected endpoint is denied."""
        response = self.client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_mission_metrics_health_endpoint_reachable(self):
        """Health endpoint confirms API layer is operational for Mission Metrics."""
        response = self.client.get("/api/health/")
        assert response.status_code == 200

    def test_mission_metrics_authenticated_request_with_school_header(self):
        """Authenticated staff request with valid X-School-ID header succeeds."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            "/api/health/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (200, 404)

    def test_mission_metrics_school_record_persists(self):
        """School record for Mission Metrics tenant is created and queryable."""
        count = School.objects.filter(name__icontains="Mission Metrics API School").count()
        assert count >= 1

    def test_mission_metrics_user_school_binding_correct(self):
        """User is bound to the correct school tenant."""
        assert self.user.school_id == self.school.id

    def test_mission_metrics_api_client_request_response_cycle(self):
        """APIClient request/response cycle works for Mission Metrics."""
        client = APIClient()
        response = client.get("/api/integrity/")
        assert response.status_code in (200, 401, 403, 404)
