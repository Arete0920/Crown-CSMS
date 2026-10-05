"""Optional adult staff guidance with tenant-bound authorization and safe auditing."""
from hashlib import sha256
import json

from django.conf import settings
from django.http import Http404
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from audit.models import AuditLog
from households.scoping import get_request_school_id
from .guidance import GuidanceInputError, build_external_payload, local_guidance
from .provider import ProviderUnavailable, generate, release_configuration, release_fingerprint
from .permissions import solomon_api_enabled

ADULT_STAFF_ROLES = {"HEAD_OF_SCHOOL", "AID_DIRECTOR", "FINANCE_DIRECTOR", "REGISTRAR", "TEACHER", "SUPPORT"}


class SolomonGuidanceThrottle(UserRateThrottle):
    scope = "solomon_guidance"
    rate = "30/min"


def _authorize(request):
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
    return school_id


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SolomonGuidanceThrottle])
def guidance_view(request):
    school_id = _authorize(request)
    if isinstance(school_id, Response):
        return school_id
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@throttle_classes([SolomonGuidanceThrottle])
def assistance_view(request):
    school_id = _authorize(request)
    if isinstance(school_id, Response):
        return school_id
    if not getattr(settings, "CROWN_SOLOMON_EXTERNAL_ENABLED", False):
        raise Http404
    try:
        build_external_payload(request.data)
        payload = local_guidance(request.data)
    except GuidanceInputError as exc:
        return Response({"detail": str(exc)}, status=400)
    metadata = {
        "school_id": str(school_id), "topic": payload["topic"],
        "policy_version": payload["policy_version"], "source_digest": payload["source_digest"],
        "human_review_acknowledged": True,
    }
    try:
        AuditLog.objects.create(
            user_id=request.user.pk, action="solomon.assistance.requested",
            model="solomon", metadata=metadata,
        )
    except Exception:
        return Response({"detail": "Guidance is temporarily unavailable."}, status=503)
    output_digest = ""
    try:
        config = release_configuration()
        result = generate(request.data, config)
        payload.update(result)
        payload.update(
            mode="generated_guidance", generated_by_ai=True,
            external_ai_status="generated_draft_requires_verification",
            release_fingerprint=release_fingerprint(config["model"], config["limit"]),
        )
        output_digest = sha256(json.dumps(result, sort_keys=True).encode("utf-8")).hexdigest()
    except ProviderUnavailable:
        payload["external_ai_status"] = "unavailable_showing_curated"
    try:
        AuditLog.objects.create(
            user_id=request.user.pk, action="solomon.assistance.completed", model="solomon",
            metadata={**metadata, "mode": payload["mode"], "output_digest": output_digest,
                      "release_fingerprint": payload.get("release_fingerprint", "")},
        )
    except Exception:
        return Response({"detail": "Guidance is temporarily unavailable."}, status=503)
    response = Response(payload)
    response["Cache-Control"] = "no-store"
    return response
