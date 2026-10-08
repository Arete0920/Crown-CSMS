"""Explicit financial authority for positive API contract fixtures."""
from core.models import CrownPermission, RolePermission, School, UserRole


def grant_finance_authority(user, school_id):
    school = School.objects.get(pk=school_id)
    role = "FINANCE_DIRECTOR"
    UserRole.objects.get_or_create(user=user, school=school, role_code=role)
    for code in ("finance.view", "finance.edit"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code=role, permission=permission)
