import pytest
from django.test import TestCase

from core.models import School
from core.tenant_models import (
    get_current_school,
    set_current_school,
    clear_current_school,
    tenant_context,
    require_tenant_context,
    TenantContextRequired,
)


class TestTenantContextGuardrails(TestCase):
    def setUp(self):
        clear_current_school()
        self.a = School.objects.create(name="Tenant A")
        self.b = School.objects.create(name="Tenant B")

    def tearDown(self):
        clear_current_school()

    def test_require_raises_when_missing(self):
        clear_current_school()
        with pytest.raises(TenantContextRequired):
            require_tenant_context()

    def test_context_sets_and_restores(self):
        clear_current_school()
        assert get_current_school() is None

        with tenant_context(self.a):
            assert get_current_school().id == self.a.id

        # restored to None
        assert get_current_school() is None

    def test_nested_context_restores_prior(self):
        clear_current_school()

        with tenant_context(self.a):
            assert get_current_school().id == self.a.id

            with tenant_context(self.b):
                assert get_current_school().id == self.b.id

            # restored to A
            assert get_current_school().id == self.a.id

        # restored to None
        assert get_current_school() is None
