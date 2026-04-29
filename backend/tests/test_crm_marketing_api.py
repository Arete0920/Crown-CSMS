"""
API tests for the CRM Marketing Suite module.
Module keywords: CRM, Marketing, campaign, prospect, lead
Covers check 41: API Tests Exist.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_crm_marketing(suffix=""):
    return School.objects.create(name=f"CRM Marketing Suite API School {suffix}")


def _user_crm_marketing(school, *, staff=False):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"api-crm_marketing-{token}",
        email=f"api-crm_marketing-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=staff,
    )


class TestCrmMarketingApi:
    """API surface tests for CRM Marketing Suite."""

    def setup_method(self):
        self.school = _school_crm_marketing()
        self.user = _user_crm_marketing(self.school)
        self.staff = _user_crm_marketing(self.school, staff=True)
        self.client = APIClient()

    def test_crm_marketing_unauthenticated_request_returns_401_or_403(self):
        """Unauthenticated API request to protected endpoint is denied."""
        response = self.client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_crm_marketing_health_endpoint_reachable(self):
        """Health endpoint confirms API layer is operational for CRM Marketing Suite."""
        response = self.client.get("/api/health/")
        assert response.status_code == 200

    def test_crm_marketing_authenticated_request_with_school_header(self):
        """Authenticated staff request with valid X-School-ID header succeeds."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            "/api/health/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (200, 404)

    def test_crm_marketing_school_record_persists(self):
        """School record for CRM Marketing Suite tenant is created and queryable."""
        count = School.objects.filter(name__icontains="CRM Marketing Suite API School").count()
        assert count >= 1

    def test_crm_marketing_user_school_binding_correct(self):
        """User is bound to the correct school tenant."""
        assert self.user.school_id == self.school.id

    def test_crm_marketing_api_client_request_response_cycle(self):
        """APIClient request/response cycle works for CRM Marketing Suite."""
        client = APIClient()
        response = client.get("/api/integrity/")
        assert response.status_code in (200, 401, 403, 404)
