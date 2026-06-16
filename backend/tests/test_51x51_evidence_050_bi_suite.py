"""Module 050 - Business Intelligence Suite - Evidence Test"""
import uuid, datetime, json
from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import School
from analytics.models import PredictiveModelRun
User = get_user_model()
TODAY = datetime.date.today()

def _school(s=""): return School.objects.create(name=f"M050 {s or uuid.uuid4().hex[:5]}", timezone="America/Chicago", is_active=True)
def _run(school): return PredictiveModelRun.objects.create(school=school, model_name="retention", run_date=TODAY, input_snapshot_date=TODAY, output_json=json.dumps({}))

class TestModule050ModelContract(TestCase):
    def test_model_importable(self): self.assertTrue(hasattr(PredictiveModelRun, "_meta"))
    def test_required_fields(self):
        names = {f.name for f in PredictiveModelRun._meta.get_fields()}
        self.assertIn("id", names)

class TestModule050ORM(TestCase):
    def setUp(self): self.school = _school("orm")
    def test_create_run(self):
        r = _run(self.school)
        self.assertIsNotNone(r.pk)
    def test_school_isolation(self):
        sa = _school("A"); sb = _school("B")
        _run(sa)
        self.assertEqual(PredictiveModelRun.objects.filter(school=sb).count(), 0)
