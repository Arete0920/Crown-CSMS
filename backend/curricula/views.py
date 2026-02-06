# curricula/views.py (read-only spine MVP)
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from households.scoping import get_request_school_id
from .models import CurriculumMap, Unit, Lesson
from .serializers import (
    CurriculumMapSerializer,
    UnitSerializer,
    LessonSerializer,
)


class CurriculumMapViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for curriculum maps.
    """
    serializer_class = CurriculumMapSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        if not school_id:
            return CurriculumMap.objects.none()
        qs = CurriculumMap.objects.filter(school_id=school_id)
        
        # Optional filtering by course
        course_id = self.request.query_params.get("course_id")
        if course_id:
            qs = qs.filter(course_id=course_id)
        
        return qs.select_related("course").order_by("course__code", "title")


class UnitViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for curriculum units.
    """
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        if not school_id:
            return Unit.objects.none()
        qs = Unit.objects.filter(school_id=school_id)
        
        # Optional filtering by curriculum_map
        curriculum_map_id = self.request.query_params.get("curriculum_map_id")
        if curriculum_map_id:
            qs = qs.filter(curriculum_map_id=curriculum_map_id)
        
        return qs.select_related("curriculum_map").order_by("curriculum_map", "sequence")


class LessonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for curriculum lessons.
    """
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        school_id = get_request_school_id(self.request)
        if not school_id:
            return Lesson.objects.none()
        qs = Lesson.objects.filter(school_id=school_id)
        
        # Optional filtering by unit
        unit_id = self.request.query_params.get("unit_id")
        if unit_id:
            qs = qs.filter(unit_id=unit_id)
        
        return qs.select_related("unit", "unit__curriculum_map").order_by("unit", "sequence")
