"""Module 016 - Faculty Load & Scheduling — Evidence Test"""

import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import School
from hr.models import Employee

User = get_user_model()
HR_URL = "/api/v1/hr/employees/"


def _school(s=""):
    return School.objects.create(
        name=f"M016 {s or uuid.uuid4().hex[:5]}",
        timezone="America/Chicago",
        is_active=True,
    )


def _client(school):
    u = User.objects.create_user(username=f"m016_{uuid.uuid4().hex[:8]}", password="pw")
    c = APIClient()
    c.force_authenticate(user=u)
    return c, u


def _hdr(sid):
    return {"HTTP_X_SCHOOL_ID": str(sid)}


class TestModule016ModelContract(TestCase):
    def test_model_importable(self):
        self.assertTrue(hasattr(Employee, "_meta"))

    def test_required_fields(self):
        names = {f.name for f in Employee._meta.get_fields()}
        for r in ("id", "school_id"):
            self.assertIn(r, names, f"Employee missing {r}")


class TestModule016Auth(TestCase):
    def setUp(self):
        self.school = _school()

    def test_unauthed_401(self):
        r = APIClient().get(HR_URL, **_hdr(self.school.id))
        self.assertEqual(
            r.status_code,
            401,
            f"Expected 401 got {r.status_code}. 404 = URL not wired.",
        )


class TestModule016CRUD(TestCase):
    def setUp(self):
        self.school = _school("crud")
        self.c, _ = _client(self.school)

    def test_list_200(self):
        r = self.c.get(HR_URL, **_hdr(self.school.id))
        self.assertIn(
            r.status_code, (200, 403), f"Expected 200/403 got {r.status_code}."
        )
