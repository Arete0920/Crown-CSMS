"""Module 021 - Competency Tracking - Evidence Test"""
import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import School
from graduation.models import GraduationRule
from core.tenant_models import tenant_context
User = get_user_model()
GRAD_URL = "/api/v1/graduation/"

def _school(s=""): return School.objects.create(name=f"M021 {s or uuid.uuid4().hex[:5]}", timezone="America/Chicago", is_active=True)

class TestModule021ModelContract(TestCase):
    def test_model_importable(self): self.assertTrue(hasattr(GraduationRule, "_meta"))
    def test_required_fields(self):
        names = {f.name for f in GraduationRule._meta.get_fields()}
        for r in ("id","school"): self.assertIn(r, names, f"GraduationRule missing {r}")

class TestModule021TenantIsolation(TestCase):
    def setUp(self): self.school_a = _school("A"); self.school_b = _school("B")
    def test_school_b_context_excludes_a(self):
        with tenant_context(self.school_a):
            GraduationRule.objects.create(school=self.school_a, name="Rule A", required_total_credits=22)
        with tenant_context(self.school_b):
            self.assertEqual(GraduationRule.objects.all().count(), 0)

class TestModule021EndpointRegistration(TestCase):
    def setUp(self): self.school = _school()
    def test_graduation_endpoint_not_500(self):
        r = APIClient().get(GRAD_URL + "audit/00000000-0000-0000-0000-000000000000/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertNotEqual(r.status_code, 500, f"500=server error, got {r.status_code}.")
