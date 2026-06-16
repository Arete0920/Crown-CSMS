"""Module 024 - Transportation & Routes — Evidence Test"""
import uuid
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import School
from transportation.models import Vehicle, Driver
User = get_user_model()

def _school(s=""): return School.objects.create(name=f"M024 {s or uuid.uuid4().hex[:5]}", timezone="America/Chicago", is_active=True)

class TestModule024ModelContract(TestCase):
    def test_vehicle_importable(self): self.assertTrue(hasattr(Vehicle, "_meta"))
    def test_driver_importable(self): self.assertTrue(hasattr(Driver, "_meta"))
    def test_vehicle_fields(self):
        names = {f.name for f in Vehicle._meta.get_fields()}
        for r in ("id","school"): self.assertIn(r, names, f"Vehicle missing {r}")
    def test_driver_fields(self):
        names = {f.name for f in Driver._meta.get_fields()}
        for r in ("id","school"): self.assertIn(r, names, f"Driver missing {r}")

class TestModule024ORM(TestCase):
    def setUp(self): self.school = _school("orm")
    def test_create_vehicle(self):
        v = Vehicle.objects.create(school=self.school, plate="ABC-123", capacity=24)
        self.assertIsNotNone(v.pk); self.assertEqual(v.school_id, self.school.id)
    def test_school_isolation(self):
        sa = _school("A"); sb = _school("B")
        Vehicle.objects.create(school=sa, plate="SA-001", capacity=10)
        self.assertEqual(Vehicle.objects.filter(school=sb).count(), 0)
