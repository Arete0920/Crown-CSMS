"""Restricted Student Care metrics adapter for release-safe aggregate access."""

from discipline.api.views import (
    DisciplineMetrics,
    STUDENT_CARE_VIEW_RESTRICTED,
    _get_school,
    _has_permission,
    _permission_denied,
)


class RestrictedDisciplineMetrics(DisciplineMetrics):
    def get(self, request):
        school = _get_school(request)
        if not _has_permission(request, school, STUDENT_CARE_VIEW_RESTRICTED):
            return _permission_denied()
        return super().get(request)
