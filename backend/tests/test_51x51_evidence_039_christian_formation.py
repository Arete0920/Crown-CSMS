"""Module 039 - Christian Formation and Tracking - Evidence Test"""

import uuid
from django.test import TestCase
from core.models import School
from spiritual_life.models import (
    StudentSpiritualProfile,
    SpiritualAssessment,
    ChapelEvent,
)


def _school(s=""):
    return School.objects.create(
        name=f"M039 {s or uuid.uuid4().hex[:5]}",
        timezone="America/Chicago",
        is_active=True,
    )


class TestModule039ModelContract(TestCase):
    def test_profile_importable(self):
        self.assertTrue(hasattr(StudentSpiritualProfile, "_meta"))

    def test_assessment_importable(self):
        self.assertTrue(hasattr(SpiritualAssessment, "_meta"))

    def test_chapel_event_importable(self):
        self.assertTrue(hasattr(ChapelEvent, "_meta"))

    def test_profile_has_school_field(self):
        names = {f.name for f in StudentSpiritualProfile._meta.get_fields()}
        self.assertIn("school", names)

    def test_profile_required_fields(self):
        names = {f.name for f in StudentSpiritualProfile._meta.get_fields()}
        for r in ("id", "school", "student"):
            self.assertIn(r, names, f"StudentSpiritualProfile missing: {r}")


class TestModule039TenantProof(TestCase):
    def test_school_field_is_required(self):
        f = StudentSpiritualProfile._meta.get_field("school")
        self.assertFalse(getattr(f, "null", True))

    def test_student_fk_to_student_model(self):
        from core.models import Student

        f = StudentSpiritualProfile._meta.get_field("student")
        self.assertEqual(f.related_model, Student)


class TestModule039ChapelEventORM(TestCase):
    def test_chapel_event_school_field(self):
        names = {f.name for f in ChapelEvent._meta.get_fields()}
        self.assertIn("school", names)

    def test_chapel_event_create_and_isolate(self):
        sa = _school("A")
        sb = _school("B")
        ChapelEvent.objects.create(
            school=sa, title="Chapel Service", event_date="2026-09-01"
        )
        self.assertEqual(ChapelEvent.objects.filter(school=sb).count(), 0)
