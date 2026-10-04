from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.data_quality import build_school_data_quality_summary
from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def school_data_quality(request):
    """Return aggregate, read-only data-quality findings for the active school."""

    school_id = get_request_school_id(request, required=True)
    school = getattr(request, "school", None)
    if school is None or str(school.id) != str(school_id):
        school = School.objects.filter(pk=school_id).first()
    if school is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not user_has_permission(request.user, "integrity.view", school=school):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    return Response(build_school_data_quality_summary(school_id=school_id))
