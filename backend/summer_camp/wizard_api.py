from __future__ import annotations

from django.db import transaction
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import School
from core.permissions import user_has_permission

from .models import SummerCampConfigWizardState
from .serializers import SummerCampProgramConfigSerializer
from .services import ensure_config
from .tenant import school_id_from_request


WIZARD_STEPS = ("Program", "Registration", "Operations", "Review")


class CampWizardSaveSerializer(serializers.Serializer):
    config = serializers.DictField(required=True, allow_empty=False)
    completed_steps = serializers.ListField(
        child=serializers.ChoiceField(choices=WIZARD_STEPS),
        required=False,
    )
    is_completed = serializers.BooleanField(required=False)

    def validate(self, attrs):
        allowed_config_fields = {
            "camp_name", "default_start_time", "default_end_time",
            "default_capacity", "default_staff_ratio", "required_form_policy",
            "billing_policy", "pickup_policy", "health_review_policy",
            "public_registration_enabled",
        }
        unexpected = set(attrs["config"]) - allowed_config_fields
        if unexpected:
            raise serializers.ValidationError({
                "config": "Unsupported or privileged camp configuration field."
            })
        steps = attrs.get("completed_steps", [])
        if steps != list(WIZARD_STEPS[:len(steps)]):
            raise serializers.ValidationError({
                "completed_steps": "Completed steps must be an ordered prefix of the setup steps."
            })
        if attrs.get("is_completed", False) and steps != list(WIZARD_STEPS):
            raise serializers.ValidationError({
                "is_completed": "All setup steps must be completed before marking the wizard complete."
            })
        return attrs


def _forbidden():
    return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)


def _has_school_grant(request, school, permission):
    user = getattr(request, "user", None)
    return bool(
        user and getattr(user, "is_authenticated", False)
        and user_has_permission(user, permission, school=school)
    )


@api_view(["GET", "POST"])
def summer_camp_setup_wizard(request):
    school_id = school_id_from_request(request, required=True)
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None:
        return _forbidden()

    if request.method == "GET":
        if not (
            _has_school_grant(request, school, "summer_camp.view")
            or _has_school_grant(request, school, "summer_camp.edit")
        ):
            return _forbidden()
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

    if not _has_school_grant(request, school, "summer_camp.edit"):
        return _forbidden()

    payload = CampWizardSaveSerializer(data=request.data)
    payload.is_valid(raise_exception=True)

    with transaction.atomic():
        config = ensure_config(school_id)
        config_serializer = SummerCampProgramConfigSerializer(
            config, data=payload.validated_data["config"], partial=True,
        )
        config_serializer.is_valid(raise_exception=True)
        config_serializer.save(school_id=school_id)

        state, _ = SummerCampConfigWizardState.objects.select_for_update().get_or_create(
            school_id=school_id,
        )
        if "completed_steps" in payload.validated_data:
            state.completed_steps = payload.validated_data["completed_steps"]
        if "is_completed" in payload.validated_data:
            state.is_completed = payload.validated_data["is_completed"]
        state.save()

    return Response(
        {
            "status": "ok",
            "config": config_serializer.data,
            "wizard": {
                "completed_steps": state.completed_steps,
                "is_completed": state.is_completed,
            },
        },
        status=status.HTTP_200_OK,
    )
