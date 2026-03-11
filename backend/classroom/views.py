from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from core.permissions import CrownModulePermission
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from core.models import School
from .models import Classroom
from .serializers import ClassroomListSerializer, ClassroomDetailSerializer


def _get_school_from_header_or_403(request) -> School:
    school_id = request.headers.get("X-School-Id") or request.META.get("HTTP_X_SCHOOL_ID")
    if not school_id:
        raise PermissionDenied("Missing X-School-Id header.")
    try:
        return School.objects.get(pk=school_id)
    except School.DoesNotExist:
        raise PermissionDenied("Invalid school context.")


class ClassroomViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only Classroom endpoints for demo + operator dashboards.
    Scoping: requires X-School-Id, filters by school.
    """
    permission_classes = [CrownModulePermission("classroom.view")]
    lookup_field = "id"

    def get_queryset(self):
        school = _get_school_from_header_or_403(self.request)
        return (
            Classroom.objects.filter(school=school, is_active=True)
            .select_related("homeroom_teacher")
            .annotate(student_count=Count("enrollments"))
            .order_by("name")
        )

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ClassroomDetailSerializer
        return ClassroomListSerializer

    @action(detail=True, methods=["get"], url_path="snapshot")
    def snapshot(self, request, id=None):
        classroom = self.get_object()
        # small payload for quick cards
        return Response(
            {
                "id": str(classroom.id),
                "name": classroom.name,
                "room": classroom.room,
                "grade_level": classroom.grade_level,
                "student_count": classroom.enrollments.count(),
                "announcements_count": classroom.announcements.count(),
                "assignments_count": classroom.assignments.count(),
            }
        )
