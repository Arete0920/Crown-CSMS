"""
Tests for tenant auto-scoping with fail-closed behavior.
"""
from django.test import TestCase, override_settings
from core.models import School
from core.tenant_models import set_current_school, get_current_school
from classroom.models import Classroom


@override_settings(TENANT_HEADER_REQUIRED=False)
class TenantAutoScopeTests(TestCase):
    def test_queryset_auto_filters_by_school(self):
        """Queries only return rows for the current school context."""
        s1 = School.objects.create(name="School A")
        s2 = School.objects.create(name="School B")

        Classroom.objects.create(name="Room A1", school=s1)
        Classroom.objects.create(name="Room A2", school=s1)
        Classroom.objects.create(name="Room B1", school=s2)

        # Set context to school A
        set_current_school(s1)
        qs = Classroom.objects.all()
        self.assertEqual(qs.count(), 2)
        self.assertEqual(set(qs.values_list("name", flat=True)), {"Room A1", "Room A2"})

        # Switch context to school B
        set_current_school(s2)
        qs = Classroom.objects.all()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Room B1")

    def test_queryset_empty_without_school_context(self):
        """FAIL-CLOSED: No school context = empty queryset (prevents leaks)."""
        s1 = School.objects.create(name="School A")
        Classroom.objects.create(name="Room A1", school=s1)

        # Clear any existing school context
        set_current_school(None)
        qs = Classroom.objects.all()
        
        # Should return ZERO rows, not all rows
        self.assertEqual(qs.count(), 0)
        self.assertIsNone(get_current_school())
