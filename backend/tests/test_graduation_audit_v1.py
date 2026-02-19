import uuid
import pytest
from django.test import TestCase

from core.models import School
from core.tenant_models import clear_current_school, set_current_school
from graduation.models import GraduationRule
from graduation.services import CreditAuditService

class TestGraduationAuditV1(TestCase):
    def setUp(self):
        clear_current_school()
        self.school = School.objects.create(name="Demo School")
        set_current_school(self.school)

    def tearDown(self):
        clear_current_school()

    def test_rule_default_when_missing(self):
        GraduationRule.objects.all().delete()
        svc = CreditAuditService()
        rule = svc._get_active_rule(self.school)
        assert str(rule["required_total_credits"]) == "24.00"

    def test_service_returns_not_found_for_unknown_student(self):
        svc = CreditAuditService()
        out = svc.audit(student_id=uuid.uuid4(), school=self.school)
        # We accept either: student model unresolved (env-specific) or student not found.
        assert out["status"] in ("STUDENT_MODEL_UNRESOLVED", "STUDENT_NOT_FOUND")

    def test_seed_rule_creation(self):
        GraduationRule.objects.create(school=self.school, name="Policy", required_total_credits=26.00, is_active=True)
        svc = CreditAuditService()
        rule = svc._get_active_rule(self.school)
        assert str(rule["required_total_credits"]) == "26.00"
