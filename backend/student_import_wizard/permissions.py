from rest_framework.exceptions import ValidationError
from core.permissions import CrownModulePermission


class ImportPermission(CrownModulePermission('rosters.edit')):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.headers.get('X-School-Id'):
            raise ValidationError('X-School-Id is required for student imports.')
        return request.user.is_active and super().has_permission(request, view)
