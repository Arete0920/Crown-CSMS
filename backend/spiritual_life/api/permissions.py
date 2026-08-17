from django.http import Http404
from rest_framework.permissions import BasePermission

from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


class SpiritualLifePermission(BasePermission):
    """Persistent tenant-scoped authority for Spiritual Life surfaces.

    The module contains student formation, prayer and pastoral data.  Django
    staff flags and authentication alone are not authority.  Cross-tenant
    attempts are concealed when the caller has no grant in the requested school.
    """

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        school_id = get_request_school_id(request, required=True)
        school = School.objects.filter(pk=school_id).first()
        if school is None:
            return False

        if user_has_permission(user, "spiritual_life.view", school=school):
            return True

        direct_school_id = getattr(user, "school_id", None)
        if direct_school_id and str(direct_school_id) != str(school_id):
            raise Http404()
        return False
