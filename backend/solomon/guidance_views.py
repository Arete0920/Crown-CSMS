"""Optional adult staff guidance with tenant-bound authorization and safe auditing."""
from django.conf import settings
from django.http import Http404
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from audit.models import AuditLog
from households.scoping import get_request_school_id
from .guidance import GuidanceInputError, local_guidance
from .permissions import solomon_api_enabled

ADULT_STAFF_ROLES = {"HEAD_OF_SCHOOL", "AID_DIRECTOR", "FINANCE_DIRECTOR", "REGISTRAR", "TEACHER", "SUPPORT"}


class SolomonGuidanceThrottle(UserRateThrottle):
    scope = "solomon_guidance"
    rate = "30/min"


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SolomonGuidanceThrottle])
def guidance_view(request):
    if not solomon_api_enabled() or not getattr(settings, "CROWN_SOLOMON_GUIDANCE_ENABLED", False):
        raise Http404
    school_id = get_request_school_id(request, required=True)
    # is_staff/superuser alone does not establish an adult school role.
    roles = set(request.user.roles.filter(school_id=school_id).values_list("role_code", flat=True))
    if "STUDENT" in roles or not roles.intersection(ADULT_STAFF_ROLES):
        raise Http404
    if request.query_params:
        return Response({"detail": "Query parameters are not supported."}, status=400)
    # Repeated form values and multipart uploads cannot collapse into accepted input.
    if request.content_type != "application/json":
        return Response({"detail": "Use a structured JSON selection."}, status=415)
    try:
        payload = local_guidance(request.data)
    except GuidanceInputError as exc:
        return Response({"detail": str(exc)}, status=400)
    try:
        AuditLog.objects.create(
            user_id=request.user.pk,
            action="solomon.guidance.read",
            model="solomon",
            metadata={
                "school_id": str(school_id),
                "topic": payload["topic"],
                "policy_version": payload["policy_version"],
                "source_digest": payload["source_digest"],
                "mode": payload["mode"],
                "human_review_acknowledged": True,
            },
        )
    except Exception:
        # Guidance requires durable accountability; never log submitted content/errors.
        return Response({"detail": "Guidance is temporarily unavailable."}, status=503)
    response = Response(payload)
    response["Cache-Control"] = "no-store"
    return response
