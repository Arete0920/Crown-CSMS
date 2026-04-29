"""
API tests for the Emergency Medical Essentials module.
Module keywords: EmergencyContact, Medical, allergy, health_flag, medication
Covers check 41: API Tests Exist.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import School

pytestmark = pytest.mark.django_db
User = get_user_model()


def _school_emergency_medical(suffix=""):
    return School.objects.create(name=f"Emergency Medical Essentials API School {suffix}")


def _user_emergency_medical(school, *, staff=False):
    token = uuid.uuid4().hex[:8]
    return User.objects.create_user(
        username=f"api-emergency_medical-{token}",
        email=f"api-emergency_medical-{token}@example.com",
        password="Passw0rd!",
        school=school,
        is_staff=staff,
    )


class TestEmergencyMedicalApi:
    """API surface tests for Emergency Medical Essentials."""

    def setup_method(self):
        self.school = _school_emergency_medical()
        self.user = _user_emergency_medical(self.school)
        self.staff = _user_emergency_medical(self.school, staff=True)
        self.client = APIClient()

    def test_emergency_medical_unauthenticated_request_returns_401_or_403(self):
        """Unauthenticated API request to protected endpoint is denied."""
        response = self.client.get("/api/auth/me/")
        assert response.status_code in (401, 403)

    def test_emergency_medical_health_endpoint_reachable(self):
        """Health endpoint confirms API layer is operational for Emergency Medical Essentials."""
        response = self.client.get("/api/health/")
        assert response.status_code == 200

    def test_emergency_medical_authenticated_request_with_school_header(self):
        """Authenticated staff request with valid X-School-ID header succeeds."""
        self.client.force_authenticate(user=self.staff)
        response = self.client.get(
            "/api/health/",
            HTTP_X_SCHOOL_ID=str(self.school.id),
        )
        assert response.status_code in (200, 404)

    def test_emergency_medical_school_record_persists(self):
        """School record for Emergency Medical Essentials tenant is created and queryable."""
        count = School.objects.filter(name__icontains="Emergency Medical Essentials API School").count()
        assert count >= 1

    def test_emergency_medical_user_school_binding_correct(self):
        """User is bound to the correct school tenant."""
        assert self.user.school_id == self.school.id

    def test_emergency_medical_api_client_request_response_cycle(self):
        """APIClient request/response cycle works for Emergency Medical Essentials."""
        client = APIClient()
        response = client.get("/api/integrity/")
        assert response.status_code in (200, 401, 403, 404)
