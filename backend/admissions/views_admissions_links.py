from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from admissions.models import AdmissionsApplication
from admissions.serializers_admissions_links import AdmissionsApplicationLinkReadSerializer


def _require_staff(request) -> Response | None:
    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return Response(
            {"detail": "Authentication credentials were not provided."}, status=401
        )

    if not (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False)):
        return Response({"detail": "Not authorized"}, status=403)

    return None


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_applications_list(request):
    denied = _require_staff(request)
    if denied is not None:
        return denied

    qs = (
        AdmissionsApplication.objects.select_related(
            "family",
            "household",
            "sis_student__person",
        )
        .order_by("-created_at")
    )

    return Response(AdmissionsApplicationLinkReadSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_application_detail(request, application_id):
    denied = _require_staff(request)
    if denied is not None:
        return denied

    qs = AdmissionsApplication.objects.select_related(
        "family",
        "household",
        "sis_student__person",
    )

    obj = get_object_or_404(qs, id=application_id)
    return Response(AdmissionsApplicationLinkReadSerializer(obj).data)
