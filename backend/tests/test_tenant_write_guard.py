"""
Tests for tenant write protection (Layer 07).
"""
import pytest
from django.test import TestCase

from core.tenant_models import set_current_school, clear_current_school, TenantWriteViolation
from core.models import School
from classroom.models import Classroom


class TestTenantWriteGuard(TestCase):
    def setUp(self):
        clear_current_school()
        # Create two tenants
        self.a = School.objects.create(name="Tenant A")
        self.b = School.objects.create(name="Tenant B")

    def tearDown(self):
        clear_current_school()

    def test_create_binds_school_when_missing(self):
        """With tenant context, creating without school should auto-bind."""
        set_current_school(self.a)
        c = Classroom(name="Room 101")  # school intentionally omitted
        c.save()
        c.refresh_from_db()
        self.assertEqual(c.school_id, self.a.id)

    def test_cross_tenant_write_blocked(self):
        """With tenant context A, saving object assigned to B must be blocked."""
        set_current_school(self.a)
        c = Classroom(name="Room X", school=self.b)
        with pytest.raises(TenantWriteViolation):
            c.save()
