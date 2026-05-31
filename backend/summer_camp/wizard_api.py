from __future__ import annotations

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import SummerCampConfigWizardState
from .serializers import SummerCampProgramConfigSerializer
from .services import ensure_config
from .tenant import school_id_from_request


@api_view(["GET", "POST"])
def summer_camp_setup_wizard(request):
    school_id = school_id_from_request(request, required=True)

    if request.method == "GET":
        config = ensure_config(school_id)
        state, _ = SummerCampConfigWizardState.objects.get_or_create(school_id=school_id)
        return Response(
            {
                "config": SummerCampProgramConfigSerializer(config).data,
                "wizard": {
                    "completed_steps": state.completed_steps,
                    "is_completed": state.is_completed,
                    "updated_at": state.updated_at.isoformat() if state.updated_at else None,
                },
            }
        )

    payload = request.data or {}
    config_data = payload.get("config") or {}
    config = ensure_config(school_id)
    serializer = SummerCampProgramConfigSerializer(config, data=config_data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save(school_id=school_id)

    state, _ = SummerCampConfigWizardState.objects.get_or_create(school_id=school_id)
    if "completed_steps" in payload:
        state.completed_steps = payload.get("completed_steps") or []
    if "is_completed" in payload:
        state.is_completed = bool(payload.get("is_completed"))
    state.save()

    return Response(
        {
            "status": "ok",
            "config": serializer.data,
            "wizard": {
                "completed_steps": state.completed_steps,
                "is_completed": state.is_completed,
            },
        },
        status=status.HTTP_200_OK,
    )
