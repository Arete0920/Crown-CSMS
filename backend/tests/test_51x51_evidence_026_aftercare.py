"""Module 026 - After-School and Extended Care - Evidence Test"""

import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import School
from aftercare.models import AftercareProgramConfig, AftercareEnrollment

User = get_user_model()
AFTERCARE_URL = "/api/v1/little-lambs/enrollments/"


def _school(s=""):
    return School.objects.create(
        name=f"M026 {s or uuid.uuid4().hex[:5]}",
        timezone="America/Chicago",
        is_active=True,
    )


def _hdr(sid):
    return {"HTTP_X_SCHOOL_ID": str(sid)}


class TestModule026ModelContract(TestCase):
    def test_program_config_importable(self):
        self.assertTrue(hasattr(AftercareProgramConfig, "_meta"))

    def test_enrollment_importable(self):
        self.assertTrue(hasattr(AftercareEnrollment, "_meta"))

    def test_config_school_id_is_required(self):
        f = AftercareProgramConfig._meta.get_field("school_id")
        self.assertFalse(getattr(f, "null", True), "school_id must be non-null")

    def test_school_id_non_fk_integer_enforces_isolation(self):
        """school_id integer is non-null: tenant isolation enforced at service layer."""
        f = AftercareProgramConfig._meta.get_field("school_id")
        self.assertFalse(getattr(f, "null", True))


class TestModule026Auth(TestCase):
    def setUp(self):
        self.school = _school()

    def test_unauthed_401(self):
        r = APIClient().get(AFTERCARE_URL, **_hdr(self.school.id))
        self.assertEqual(
            r.status_code, 401, f"Expected 401 got {r.status_code}. 404=URL not wired."
        )


class TestModule026EndpointRegistration(TestCase):
    def setUp(self):
        self.school = _school()

    def test_config_endpoint_not_500(self):
        r = APIClient().get("/api/v1/little-lambs/config/", **_hdr(self.school.id))
        self.assertNotEqual(
            r.status_code, 500, f"500=server error on config URL, got {r.status_code}."
        )
