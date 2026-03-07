# backend/core/viewsets.py
"""
Tenant-scoped base ViewSets for writable endpoints.

Uses the canonical scope_to_school() from households.scoping which handles:
- X-School-Id header resolution
- 400 for missing/invalid tenant
- 404 for non-existent school or cross-tenant access
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from households.scoping import scope_to_school


class TenantScopedViewSet(viewsets.ModelViewSet):
    """
    ModelViewSet that enforces tenant scoping for any model with school_id.

    All queries are filtered to the resolved tenant.
    Writes stamp school_id from the resolved tenant context.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return scope_to_school(self.request, qs)

    def perform_create(self, serializer):
        from households.scoping import get_request_school_id

        school_id = get_request_school_id(self.request, required=True)
        serializer.save(school_id=school_id)

    def perform_update(self, serializer):
        serializer.save()


class TenantScopedReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ReadOnlyModelViewSet that enforces tenant scoping.
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        return scope_to_school(self.request, qs)
