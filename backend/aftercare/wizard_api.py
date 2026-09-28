from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import School
from core.permissions import user_has_permission

from .serializers import AftercareProgramConfigSerializer
from .services import ensure_config
from .tenant import school_id_from_request


def _has_permission(request, code: str, school: School) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return user_has_permission(user, code, school=school)


def _forbidden():
    return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


@api_view(["GET", "POST"])
def aftercare_setup_wizard(request):
    """Read or update the tenant's canonical extended-care program config."""
    school_id = school_id_from_request(request, required=True)
    # Permission scope must match the canonical tenant used for config access.
    school = School.objects.filter(pk=school_id).first()
    if school is None:
        return _forbidden()

    if request.method == "GET":
        if not _has_permission(request, "extended_care.view", school):
            return _forbidden()
        cfg = ensure_config(school_id)
        return Response({"config": AftercareProgramConfigSerializer(cfg).data})

    if not _has_permission(request, "extended_care.edit", school):
        return _forbidden()

    cfg = ensure_config(school_id)
    config_data = request.data.get("config", request.data)
    serializer = AftercareProgramConfigSerializer(cfg, data=config_data, partial=True)
    serializer.is_valid(raise_exception=True)
    cfg = serializer.save()

    return Response(
        {"status": "ok", "config": AftercareProgramConfigSerializer(cfg).data},
        status=status.HTTP_200_OK,
    )
