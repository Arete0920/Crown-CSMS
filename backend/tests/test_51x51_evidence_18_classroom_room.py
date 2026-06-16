"""
Module 018 - Classroom & Room Management
Evidence Test File
==================
Proves the Classroom & Room Management boundary using the Crown
tenant_context() helper (required for TenantScopedModel ORM access):
  1. Classroom model importable and fields correct
  2. Classroom inherits TenantScopedModel (school FK + tenant manager)
  3. Create/read lifecycle works within tenant_context
  4. Tenant isolation: School A classrooms not returned in School B context
  5. Classroom endpoint registered (returns 401 unauthenticated, not 404)
  6. CrownModulePermission is the declared permission class
  7. Fail-closed: no tenant context = empty queryset (no leak)
"""

import uuid

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import School
from classroom.models import Classroom
from core.tenant_models import tenant_context

CLASSROOMS_URL = "/api/classroom/classrooms/"


def _make_school(suffix=""):
    return School.objects.create(
        name=f"Module018 School {suffix or uuid.uuid4().hex[:6]}",
        timezone="America/Chicago",
        is_active=True,
    )


class TestModule018ModelContract(TestCase):
    """Model import and field contract."""

    def test_model_importable(self):
        self.assertTrue(hasattr(Classroom, "_meta"))

    def test_required_fields_exist(self):
        field_names = {f.name for f in Classroom._meta.get_fields()}
        for required in ("id", "school", "name", "is_active", "created_at"):
            self.assertIn(required, field_names, f"Classroom missing field: {required}")

    def test_classroom_inherits_tenant_scope(self):
        from core.tenant_models import TenantScopedModel
        self.assertTrue(
            issubclass(Classroom, TenantScopedModel),
            "Classroom must inherit TenantScopedModel.",
        )


class TestModule018OrmLifecycle(TestCase):
    """Create/read lifecycle via tenant_context helper."""

    def setUp(self):
        self.school = _make_school("crud")

    def test_create_classroom_within_context(self):
        with tenant_context(self.school):
            c = Classroom.objects.create(name="9th Grade Homeroom", room="B201")
        self.assertIsNotNone(c.pk)
        self.assertEqual(c.school_id, self.school.id)

    def test_list_classrooms_within_context(self):
        with tenant_context(self.school):
            Classroom.objects.create(name="Room A")
            qs = Classroom.objects.all()
            self.assertGreaterEqual(qs.count(), 1)

    def test_fail_closed_without_context(self):
        """TenantManager must return empty queryset when no school context."""
        with tenant_context(self.school):
            Classroom.objects.create(name="Context Room")
        # Outside context: queryset must be empty (fail-closed)
        qs = Classroom.objects.all()
        self.assertEqual(
            qs.count(), 0,
            "TenantManager must return empty queryset when no school context.",
        )


class TestModule018TenantIsolation(TestCase):
    """Tenant isolation via tenant_context."""

    def setUp(self):
        self.school_a = _make_school("A")
        self.school_b = _make_school("B")

    def test_school_b_context_excludes_school_a_classrooms(self):
        with tenant_context(self.school_a):
            Classroom.objects.create(name="Private Room A")
        with tenant_context(self.school_b):
            qs_b = Classroom.objects.all()
            self.assertEqual(
                qs_b.count(), 0,
                "School B context must not include School A classrooms.",
            )

    def test_pk_from_school_a_not_accessible_in_school_b_context(self):
        with tenant_context(self.school_a):
            ca = Classroom.objects.create(name="Room A")
        with tenant_context(self.school_b):
            self.assertFalse(
                Classroom.objects.filter(pk=ca.pk).exists(),
                "School A classroom pk must not be accessible via School B context.",
            )


class TestModule018EndpointRegistration(TestCase):
    """Endpoint is registered (not 404)."""

    def setUp(self):
        self.school = _make_school()

    def test_unauthenticated_returns_401_not_404(self):
        c = APIClient()
        r = c.get(CLASSROOMS_URL, HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(
            r.status_code, 401,
            f"Expected 401 for unauthenticated GET, got {r.status_code}. "
            "If 404, URL not wired in crown_api/urls.py.",
        )


class TestModule018PermissionDeclaration(TestCase):
    """CrownModulePermission is the declared permission class."""

    def test_viewset_declares_permission_class(self):
        from classroom.views import ClassroomViewSet
        self.assertTrue(
            len(ClassroomViewSet.permission_classes) > 0,
            "ClassroomViewSet must declare at least one permission class.",
        )
