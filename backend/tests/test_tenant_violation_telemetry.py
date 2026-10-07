import pytest
from django.test import TestCase

from core.models import School
from core.tenant_models import (
    tenant_context,
    set_current_school,
    clear_current_school,
    require_tenant_context,
    TenantContextRequired,
    TenantWriteViolation,
    TenantBulkOpViolation,
)
from classroom.models import Classroom


class TestTenantViolationTelemetry(TestCase):
    def setUp(self):
        clear_current_school()
        self.a = School.objects.create(name="Tenant A")
        self.b = School.objects.create(name="Tenant B")
        with tenant_context(self.a):
            Classroom.objects.create(name="A-1", school=self.a)
        with tenant_context(self.b):
            Classroom.objects.create(name="B-1", school=self.b)

    def tearDown(self):
        clear_current_school()

    def test_logs_context_required_violation(self):
        clear_current_school()
        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
            with pytest.raises(TenantContextRequired):
                require_tenant_context()
        assert any("TENANT_VIOLATION" in m for m in logs.output)

    def test_logs_cross_tenant_write_violation(self):
        set_current_school(self.a)
        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
            with pytest.raises(TenantWriteViolation):
                Classroom(name="X", school=self.b).save()
        assert any("TENANT_VIOLATION" in m for m in logs.output)

    def test_logs_bulk_update_missing_context(self):
        clear_current_school()
        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
            with pytest.raises(TenantBulkOpViolation):
                Classroom.objects.update(name="NOPE")
        assert any("TENANT_VIOLATION" in m for m in logs.output)

    def test_logs_bulk_delete_missing_context(self):
        clear_current_school()
        with self.assertLogs("core.tenant_models", level="WARNING") as logs:
            with pytest.raises(TenantBulkOpViolation):
                Classroom.objects.all().delete()
        assert any("TENANT_VIOLATION" in m for m in logs.output)
