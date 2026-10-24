"""Canonical read-only household, guardian and student privacy boundaries."""

from django.db.models import Prefetch
from rest_framework import permissions, viewsets

from core.scoping import (
    DOMAIN_GUARDIANS,
    DOMAIN_HOUSEHOLDS,
    DOMAIN_STUDENTS,
    scope_queryset,
    scope_serializer_fields,
    scoped_serializer_context,
)
from .models import Guardian, Household, Student
from .scoping import get_request_school_id, scope_to_school
from .serializers import GuardianSerializer, HouseholdSerializer, StudentSerializer


class ScopedReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
    """Scope tenant, row, and fields before any record is serialized."""

    permission_classes = [permissions.IsAuthenticated]
    crown_domain = None

    def get_queryset(self):
        tenant_rows = scope_to_school(self.request, super().get_queryset())
        school_id = get_request_school_id(self.request)
        if self.crown_domain == DOMAIN_HOUSEHOLDS:
            # FK membership alone does not prove a related row belongs to
            # this school. Prefetch only consistent rows for nested output.
            tenant_rows = tenant_rows.prefetch_related(
                Prefetch(
                    "guardians",
                    queryset=Guardian.objects.filter(
                        school_id=school_id, household__school_id=school_id,
                    ),
                ),
                Prefetch(
                    "students",
                    queryset=Student.objects.filter(
                        school_id=school_id, household__school_id=school_id,
                    ),
                ),
            )
        elif self.crown_domain in {DOMAIN_GUARDIANS, DOMAIN_STUDENTS}:
            # Reject inconsistent historical or bypass-written relations on
            # both list and detail, even when the row's school_id is valid.
            tenant_rows = tenant_rows.filter(household__school_id=school_id)
        return scope_queryset(self.request.user, tenant_rows, self.crown_domain, school_id=school_id)

    def get_serializer_context(self):
        return scoped_serializer_context(self.crown_domain, super().get_serializer_context())

    def get_serializer(self, *args, **kwargs):
        serializer = super().get_serializer(*args, **kwargs)
        target = serializer.child if hasattr(serializer, "child") else serializer
        scope_serializer_fields(
            self.request.user, target, school_id=get_request_school_id(self.request)
        )
        return serializer


class HouseholdViewSet(ScopedReadOnlyModelViewSet):
    queryset = Household.objects.order_by("name")
    serializer_class = HouseholdSerializer
    crown_domain = DOMAIN_HOUSEHOLDS


class GuardianViewSet(ScopedReadOnlyModelViewSet):
    queryset = Guardian.objects.select_related("household").order_by("last_name", "first_name")
    serializer_class = GuardianSerializer
    crown_domain = DOMAIN_GUARDIANS


class StudentViewSet(ScopedReadOnlyModelViewSet):
    queryset = Student.objects.select_related("household").order_by("last_name", "first_name")
    serializer_class = StudentSerializer
    crown_domain = DOMAIN_STUDENTS
