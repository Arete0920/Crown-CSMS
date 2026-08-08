from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication
from admissions.serializers_admissions_links import AdmissionsApplicationLinkReadSerializer
from core.models import School
from core.permissions import user_has_permission
from households.scoping import get_request_school_id


def _require_admissions_view(request, school) -> Response | None:
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )
    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        return None
    if user_has_permission(user, "admissions.view", school=school):
        return None
    return Response({"detail": "Permission denied."}, status=403)


@extend_schema(
    responses=AdmissionsApplicationLinkReadSerializer(many=True),
    tags=["Admissions"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_applications_list(request):
    school_id = get_request_school_id(request, required=True)
    school = School.objects.get(pk=school_id)

    denied = _require_admissions_view(request, school)
    if denied is not None:
        return denied

    qs = (
        AdmissionsApplication.objects.select_related(
            "family",
            "household",
            "sis_student__person",
        )
        .prefetch_related("household__members__person")
        .filter(school=school)
        .order_by("-created_at")
    )

    return Response(AdmissionsApplicationLinkReadSerializer(qs, many=True).data)


@extend_schema(
    parameters=[
        OpenApiParameter(
            name="application_id",
            location=OpenApiParameter.PATH,
            required=True,
            type=OpenApiTypes.INT,
        )
    ],
    responses=AdmissionsApplicationLinkReadSerializer,
    tags=["Admissions"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_application_detail(request, application_id):
    school_id = get_request_school_id(request, required=True)
    school = School.objects.get(pk=school_id)

    denied = _require_admissions_view(request, school)
    if denied is not None:
        return denied

    qs = AdmissionsApplication.objects.select_related(
        "family",
        "household",
        "sis_student__person",
    ).prefetch_related("household__members__person")

    obj = get_object_or_404(qs, id=application_id, school=school)
    return Response(AdmissionsApplicationLinkReadSerializer(obj).data)
