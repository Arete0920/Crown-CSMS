from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SectionRow, CourseRow


class AcademicsROSectionSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    term = serializers.CharField(allow_blank=True, allow_null=True)
    period = serializers.CharField(allow_blank=True, allow_null=True)
    teacher_id = serializers.CharField(allow_null=True)
    teacher_name = serializers.CharField(allow_blank=True, allow_null=True)


def _get_user_context(request):
    """
    Extract user context from request headers.
    Replace later with central request context helper when available.
    
    Note: UUIDs in headers may have hyphens, but DB stores as char(32) without hyphens.
    Strip hyphens to match DB format.
    """
    role = (
        getattr(request, "crown_role", None) 
        or request.headers.get("X-Role") 
        or request.headers.get("x-role") 
        or ""
    ).strip().lower()
    
    user_id = (
        getattr(request, "crown_user_id", None) 
        or request.headers.get("X-User-Id") 
        or request.headers.get("x-user-id")
        or ""
    ).strip().replace("-", "")
    
    school_id = (
        getattr(request, "crown_school_id", None) 
        or request.headers.get("X-School-Id") 
        or request.headers.get("x-school-id")
        or ""
    ).strip().replace("-", "")
    
    return (role, user_id, school_id)


class SectionsList(APIView):
    """
    Read-only sections list endpoint.
    
    Auth: bypasses DRF global auth to use manual header-based gate.
    This is a controlled demo gate, not an open endpoint.
    """
    authentication_classes = []
    permission_classes = []

    @extend_schema(tags=["academics"], responses=AcademicsROSectionSerializer(many=True))
    def get(self, request):
        role, user_id, school_id = _get_user_context(request)

        # Manual header gate
        if not school_id:
            return Response(
                {"detail": "Missing school context (X-School-Id header required)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user_id:
            return Response(
                {"detail": "Missing user context (X-User-Id header required)."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Role allowlist
        ALLOWED_ROLES = ("admin", "staff", "teacher", "student", "parent")
        if not role or role not in ALLOWED_ROLES:
            return Response(
                {"detail": f"Invalid or missing role. X-Role header must be one of: {', '.join(ALLOWED_ROLES)}."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Query sections using ORM adapter (CharField IDs, not UUIDs)
        sections = list(
            SectionRow.objects.filter(school_id=school_id).order_by("id")[:200]
        )
        
        # Build course lookup for meaningful names
        course_ids = [s.course_id for s in sections if s.course_id]
        courses = {c.id: c for c in CourseRow.objects.filter(id__in=course_ids)}

        out = []
        for s in sections:
            course = courses.get(s.course_id)
            course_name = course.name if course else "Unknown Course"
            
            out.append({
                "id": s.id,
                "name": course_name,
                "term": s.term,
                "period": "",  # Not in current schema
                "teacher_id": None,  # Not in current schema (only teacher_name exists)
                "teacher_name": s.teacher_name,
            })

        return Response(out)
