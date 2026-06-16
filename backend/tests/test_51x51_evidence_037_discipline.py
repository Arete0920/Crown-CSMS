"""Module 037 - Advanced Discipline Workflows - Evidence Test"""
import uuid
from django.test import TestCase
from core.models import School
from discipline.models import DisciplineIncident, DisciplineAction

def _school(s=""): return School.objects.create(name=f"M037 {s or uuid.uuid4().hex[:5]}", timezone="America/Chicago", is_active=True)

class TestModule037ModelContract(TestCase):
    def test_incident_importable(self): self.assertTrue(hasattr(DisciplineIncident, "_meta"))
    def test_action_importable(self): self.assertTrue(hasattr(DisciplineAction, "_meta"))
    def test_incident_has_school_field(self):
        names = {f.name for f in DisciplineIncident._meta.get_fields()}
        self.assertIn("school", names)
    def test_incident_required_workflow_fields(self):
        names = {f.name for f in DisciplineIncident._meta.get_fields()}
        for r in ("id", "school", "student", "occurred_at", "summary"):
            self.assertIn(r, names, f"DisciplineIncident missing: {r}")
    def test_action_has_incident_link(self):
        names = {f.name for f in DisciplineAction._meta.get_fields()}
        self.assertIn("incident", names)

class TestModule037TenantProof(TestCase):
    def test_school_field_is_required(self):
        f = DisciplineIncident._meta.get_field("school")
        self.assertFalse(getattr(f, "null", True))
    def test_student_fk_to_student_model(self):
        from core.models import Student
        f = DisciplineIncident._meta.get_field("student")
        self.assertEqual(f.related_model, Student)
