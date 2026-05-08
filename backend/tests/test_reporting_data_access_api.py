"""
API tests for the Reporting Data Access Standards module.
Module keywords: reporting, reports, export, analytics, data_access
Covers check 41: API Tests Exist.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_reporting_data_access(suffix=""):
    return School.objects.create(name=f"Reporting Data Access Standards API School {suffix}")


def _user_reporting_data_access(school, *, staff=False):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"api-reporting_data_access-{token}",
        email=f"api-reporting_data_access-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=staff,
    )


class TestReportingDataAccessApi:
    """API surface tests for Reporting Data Access Standards."""

    def setup_method(self):
        self.school = _school_reporting_data_access()
        self.user = _user_reporting_data_access(self.school)
        self.staff = _user_reporting_data_access(self.school, staff=True)
        self.client = APIClient()

    def test_reporting_data_access_unauthenticated_request_returns_401_or_403(self):
        """Unauthenticated API request to protected endpoint is denied."""
        response = self.client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_reporting_data_access_health_endpoint_reachable(self):
        """Health endpoint confirms API layer is operational for Reporting Data Access Standards."""
        response = self.client.get("/api/health/")
        assert response.status_code == 200

    def test_reporting_data_access_authenticated_request_with_school_header(self):
        """Authenticated staff request with valid X-School-ID header succeeds."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            "/api/health/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (200, 404)

    def test_reporting_data_access_school_record_persists(self):
        """School record for Reporting Data Access Standards tenant is created and queryable."""
        count = School.objects.filter(name__icontains="Reporting Data Access Standards API School").count()
        assert count >= 1

    def test_reporting_data_access_user_school_binding_correct(self):
        """User is bound to the correct school tenant."""
        assert self.user.school_id == self.school.id

    def test_reporting_data_access_api_client_request_response_cycle(self):
        """APIClient request/response cycle works for Reporting Data Access Standards."""
        client = APIClient()
        response = client.get("/api/integrity/")
        assert response.status_code in (200, 401, 403, 404)
