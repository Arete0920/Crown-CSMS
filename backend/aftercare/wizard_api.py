from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .tenant import school_id_from_request
from .models import AftercareProgramConfig
from .serializers import AftercareProgramConfigSerializer
from .services import ensure_config


# CANON_RBAC_TODO: replace with your real admin check
def require_admin(request) -> bool:
    return True


@api_view(["GET", "POST"])
def aftercare_setup_wizard(request):
    """
    CrownMagus Aftercare Setup Wizard endpoint.
    GET  — returns current program config for pre-population.
    POST — validates + saves config; marks wizard complete.
    """
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        cfg = ensure_config(school_id)
        return Response({"config": AftercareProgramConfigSerializer(cfg).data})

    if not require_admin(request):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    cfg = ensure_config(school_id)
    config_data = request.data.get("config", request.data)  # accept both wrapped and flat
    ser = AftercareProgramConfigSerializer(cfg, data=config_data, partial=True)
    ser.is_valid(raise_exception=True)
    ser.save(school_id=school_id)

    # CANON_WIZARD_COMPLETE_TODO: record wizard completion in your registry if needed
    # e.g. mark_wizard_complete(school_id=school_id, key="aftercare_setup")

    return Response({"status": "ok", "config": ser.data}, status=status.HTTP_200_OK)
