from django.conf import settings
from rest_framework import permissions, viewsets
from core.models import UserRole
from core.scoping import DOMAIN_STUDENTS, scope_queryset
from .models import Guardian, Household, Student
from .scoping import scope_to_school
from .serializers import GuardianSerializer, HouseholdSerializer, StudentSerializer


def _user_has_parent_role(user, school_id):
    """Return True if user holds a PARENT role at this school."""
    user_id = getattr(user, "id", None)
    if not user_id:
        return False
    roles = UserRole.objects.filter(user_id=user_id, role_code="PARENT")
    if school_id:
        roles = roles.filter(school_id=school_id)
    return roles.exists()


class ScopedReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
	"""
	Read-only spine module viewset with strict school scoping.
	"""
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		qs = super().get_queryset()
		return scope_to_school(self.request, qs)


class HouseholdViewSet(ScopedReadOnlyModelViewSet):
	queryset = Household.objects.order_by("name")
	serializer_class = HouseholdSerializer

	def get_queryset(self):
		# Parent class (ScopedReadOnlyModelViewSet) handles school scoping via scope_to_school()
		# We only add optional guardian-level filtering here
		qs = super().get_queryset()

		# Apply guardian scoping if enabled - PARENT role users only
		if getattr(settings, "HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED", True):
			user = self.request.user
			school = getattr(self.request, "school", None)
			school_id = school.id if school else None
			if _user_has_parent_role(user, school_id):
				email = getattr(user, "email", None)
				if not email:
					return qs.none()
				qs = qs.filter(guardians__email__iexact=email).distinct()

		return qs


class GuardianViewSet(ScopedReadOnlyModelViewSet):
	queryset = Guardian.objects.select_related("household").all().order_by("last_name", "first_name")
	serializer_class = GuardianSerializer


class StudentViewSet(ScopedReadOnlyModelViewSet):
	queryset = Student.objects.select_related("household").all().order_by("last_name", "first_name")
	serializer_class = StudentSerializer

	def get_queryset(self):
		# Tenant (school) scoping comes first - enforced by scope_to_school.
		# Role-based row scoping is delegated entirely to core.scoping.scope_queryset.
		# DO NOT add inline role checks here - add them to core/scoping.py instead.
		qs = Student.objects.select_related("household").all()
		qs = scope_to_school(self.request, qs)
		if not getattr(settings, "HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED", True):
			return qs
		school = getattr(self.request, "school", None)
		school_id = school.id if school else None
		return scope_queryset(self.request.user, qs, DOMAIN_STUDENTS, school_id=school_id)


