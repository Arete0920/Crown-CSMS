from django.conf import settings
from rest_framework import permissions, viewsets
from .models import Guardian, Household, Student
from .scoping import scope_to_school
from .serializers import GuardianSerializer, HouseholdSerializer, StudentSerializer


class ScopedReadOnlyModelViewSet(viewsets.ReadOnlyModelViewSet):
	"""
	Read-only spine module viewset with strict school scoping.
	"""
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		qs = super().get_queryset()
		return scope_to_school(self.request, qs)


class HouseholdViewSet(ScopedReadOnlyModelViewSet):
	queryset = Household.objects.all().order_by("name")
	serializer_class = HouseholdSerializer

	def get_queryset(self):
		qs = Household.objects.all()
		
		# Apply school scoping
		qs = scope_to_school(self.request, qs)
		
		# Apply guardian scoping if enabled (opt-in)
		if getattr(settings, "HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED", False):
			user = self.request.user
			if not getattr(user, "is_staff", False):
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
		qs = Student.objects.select_related("household").all()
		
		# Apply school scoping
		qs = scope_to_school(self.request, qs)
		
		# Apply guardian scoping if enabled (opt-in)
		if getattr(settings, "HOUSEHOLDS_GUARDIAN_SCOPE_ENABLED", False):
			user = self.request.user
			if not getattr(user, "is_staff", False):
				email = getattr(user, "email", None)
				if not email:
					return qs.none()
				# Students must be in households where guardian email matches
				qs = qs.filter(household__guardians__email__iexact=email).distinct()
		
		return qs
