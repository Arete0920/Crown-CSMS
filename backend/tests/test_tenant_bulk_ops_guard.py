import pytest
from django.test import TestCase

from core.tenant_models import tenant_context, set_current_school, clear_current_school, TenantBulkOpViolation
from core.models import School
from classroom.models import Classroom


class TestTenantBulkOpsGuard(TestCase):
    def setUp(self):
        clear_current_school()
        self.a = School.objects.create(name="Tenant A")
        self.b = School.objects.create(name="Tenant B")

        # Seed one row in each tenant
        with tenant_context(self.a):
            Classroom.objects.create(name="A-1", school=self.a)
        with tenant_context(self.b):
            Classroom.objects.create(name="B-1", school=self.b)

    def tearDown(self):
        clear_current_school()

    def test_bulk_update_requires_tenant_context(self):
        clear_current_school()
        with pytest.raises(TenantBulkOpViolation):
            Classroom.objects.update(name="NOPE")

    def test_bulk_delete_requires_tenant_context(self):
        clear_current_school()
        with pytest.raises(TenantBulkOpViolation):
            Classroom.objects.all().delete()

    def test_bulk_ops_scoped_to_current_tenant(self):
        # With tenant A context, bulk ops must only touch tenant A rows
        set_current_school(self.a)

        # Update should only affect A rows
        Classroom.objects.update(name="RENAMED")
        
        # Verify A row was updated
        assert Classroom.objects.filter(name="RENAMED").count() == 1
        
        # Verify B row unchanged (clear context to see all rows)
        clear_current_school()
        b_classroom = Classroom._base_manager.get(school=self.b)
        assert b_classroom.name == "B-1"
        
        # Delete should only delete A rows (set context back to A)
        set_current_school(self.a)
        Classroom.objects.all().delete()
        
        # Verify only B row remains (check via base manager)
        clear_current_school()
        remaining = list(Classroom._base_manager.values_list("school_id", flat=True))
        assert remaining == [self.b.id]
