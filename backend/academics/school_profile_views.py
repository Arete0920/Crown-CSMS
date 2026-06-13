from __future__ import annotations

from drf_spectacular.utils import extend_schema
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import School, UserRole
from households.scoping import get_request_school_id

from .serializers import SchoolSerializer


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    user_id = getattr(user, "id", None)
    if not user_id:
        return set()
    return set(
        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list(
            "role_code", flat=True
        )
    )


class SchoolProfileView(APIView):
    """
    Tenant-scoped school profile endpoint.

    GET  /api/v1/school/  — returns the authenticated user's school profile.
    PATCH /api/v1/school/ — updates writable school settings; restricted to
                            superusers and HEAD_OF_SCHOOL role holders.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SchoolSerializer)
    def get(self, request):
        school_id = get_request_school_id(request, required=True)
        school = get_object_or_404(School, pk=school_id)
        return Response(SchoolSerializer(school).data)

    @extend_schema(request=SchoolSerializer, responses=SchoolSerializer)
    def patch(self, request):
        school_id = get_request_school_id(request, required=True)
        user = getattr(request, "user", None)
        roles = _role_codes(user, school_id)
        if not (
            getattr(user, "is_superuser", False)
            or "HEAD_OF_SCHOOL" in roles
        ):
            raise PermissionDenied(
                "Only superusers or HEAD_OF_SCHOOL role holders may update school settings."
            )
        school = get_object_or_404(School, pk=school_id)
        serializer = SchoolSerializer(school, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
