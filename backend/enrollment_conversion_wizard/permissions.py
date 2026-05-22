from rest_framework.response import Response

from core.permissions import user_has_permission


def can_manage_enrollment_conversion(user, school) -> bool:
	if not getattr(user, "is_authenticated", False):
		return False
	if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
		return True

	return user_has_permission(user, "admissions.edit", school=school) or user_has_permission(
		user,
		"admin.view",
		school=school,
	)


def require_enrollment_conversion_access(request, school):
	if can_manage_enrollment_conversion(request.user, school):
		return None
	return Response({"detail": "Permission denied."}, status=403)
