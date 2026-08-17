from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.permissions import user_has_permission
from .serializers import AftercareProgramConfigSerializer
from .services import ensure_config
from .tenant import school_id_from_request


def require_admin(request) -> bool:
    user = getattr(request, "user", None)
    school = getattr(request, "school", None)
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and school is not None
        and (
            getattr(user, "is_superuser", False)
            or user_has_permission(user, "aftercare.edit", school=school)
        )
    )


@api_view(["GET", "POST"])
def aftercare_setup_wizard(request):
    school_id = school_id_from_request(request, required=True)
    if request.method == "GET":
        if not require_admin(request):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        cfg = ensure_config(school_id)
        return Response({"config": AftercareProgramConfigSerializer(cfg).data})

    if not require_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    cfg = ensure_config(school_id)
    config_data = request.data.get("config", request.data)
    ser = AftercareProgramConfigSerializer(cfg, data=config_data, partial=True, context={"request": request})
    ser.is_valid(raise_exception=True)
    ser.save(school_fk_id=school_id, school_id=None)
    return Response({"status": "ok", "config": ser.data}, status=status.HTTP_200_OK)
