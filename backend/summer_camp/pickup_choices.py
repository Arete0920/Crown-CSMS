"""School-scoped authorized pickup choices for staff-verified Summer Camp release.

A read-only contact selector, not checkout authority. The custody service must
recheck the chosen contact and record the authenticated staff verifier.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import School
from core.permissions import user_has_permission

from .models import SummerCampEnrollment, SummerCampPickupContact
from .tenant import school_id_from_request
from .entitlements import camp_entitlement_error


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def pickup_choices(request, enrollment_id):
    school_id = school_id_from_request(request, required=True)
    denied = camp_entitlement_error(school_id)
    if denied is not None:
        return denied
    school = School.objects.filter(pk=school_id, is_active=True).first()
    user = getattr(request, "user", None)
    if not (
        school and user and getattr(user, "is_authenticated", False)
        and getattr(user, "is_active", False)
        and getattr(user, "school_id", None) == school_id
        and user_has_permission(user, "summer_camp.edit", school=school)
    ):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    enrollment = SummerCampEnrollment.objects.filter(
        pk=enrollment_id, school_id=school_id,
        session__school_id=school_id, student__school_id=school_id,
        student__is_active=True, status="REGISTERED",
    ).values("id", "session_id", "student_id").first()
    if enrollment is None:
        return Response({"detail": "No current camp enrollment."}, status=status.HTTP_404_NOT_FOUND)

    active = SummerCampEnrollment.objects.filter(
        school_id=school_id, session_id=enrollment["session_id"],
        student_id=enrollment["student_id"], status="REGISTERED",
    ).count()
    if active != 1:
        return Response(
            {"detail": "Enrollment needs manual reconciliation."},
            status=status.HTTP_409_CONFLICT,
        )

    contacts = list(
        SummerCampPickupContact.objects.filter(
            school_id=school_id, enrollment_id=enrollment_id, is_active=True,
        ).order_by("name", "pk").values("id", "name", "relationship")
    )
    return Response({"enrollment_id": enrollment_id, "contacts": contacts})
