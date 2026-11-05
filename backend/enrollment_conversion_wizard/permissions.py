from rest_framework.response import Response

from core.permissions import user_has_permission


def can_manage_enrollment_conversion(user, school) -> bool:
	# Staff/superuser Django flags are not a tenant-specific enrollment grant.
	# Require an explicit, active school-scoped role even for privileged users.
	if (
		school is None
		or not getattr(school, "is_active", False)
		or not getattr(user, "is_authenticated", False)
		or not getattr(user, "is_active", False)
	):
		return False

	# admin.view is read-only by itself; enrollment conversion changes records.
	# Preserve director actions only with both explicit school-scoped grants.
	return user_has_permission(user, "admissions.edit", school=school) or (
		user_has_permission(user, "admin.view", school=school)
		and user_has_permission(user, "director.actions", school=school)
	)


def require_enrollment_conversion_access(request, school):
	if can_manage_enrollment_conversion(request.user, school):
		return None
	return Response({"detail": "Permission denied."}, status=403)
