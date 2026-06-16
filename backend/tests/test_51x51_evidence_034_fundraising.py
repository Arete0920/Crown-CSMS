"""Module 034 - Fundraising & Giving - Evidence Test"""
import uuid
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from core.models import School
from advancement.models import Donor, Campaign
User = get_user_model()
ADVANCEMENT_URL = "/api/v1/advancement/donors/"

def _school(s=""):
    return School.objects.create(name=f"M034 {s or uuid.uuid4().hex[:5]}", timezone="America/Chicago", is_active=True)

def _hdr(sid): return {"HTTP_X_SCHOOL_ID": str(sid)}

class TestModule034ModelContract(TestCase):
    def test_donor_importable(self): self.assertTrue(hasattr(Donor, "_meta"))
    def test_campaign_importable(self): self.assertTrue(hasattr(Campaign, "_meta"))
    def test_donor_has_school_id(self):
        names = {f.name for f in Donor._meta.get_fields()}
        self.assertIn("school_id", names)
    def test_donor_has_name(self):
        names = {f.name for f in Donor._meta.get_fields()}
        self.assertIn("name", names)

class TestModule034Auth(TestCase):
    def setUp(self): self.school = _school()
    def test_unauthed_401(self):
        r = APIClient().get(ADVANCEMENT_URL, **_hdr(self.school.id))
        self.assertEqual(r.status_code, 401, f"Expected 401 got {r.status_code}.")

class TestModule034ORM(TestCase):
    def setUp(self): self.school = _school("orm")
    def test_create_donor(self):
        d = Donor.objects.create(school_id=self.school.id, name="Jane Smith")
        self.assertIsNotNone(d.pk)
        self.assertEqual(str(d.school_id), str(self.school.id))
    def test_school_id_isolation(self):
        sa = _school("A"); sb = _school("B")
        Donor.objects.create(school_id=sa.id, name="A Donor")
        self.assertEqual(Donor.objects.filter(school_id=sb.id).count(), 0)
