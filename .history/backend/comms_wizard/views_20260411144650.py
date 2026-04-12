from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from comms.models import OutboxMessage
from households.scoping import get_request_school_id

from .models import CommsWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(
        CommsWizardSession, id=session_id, school__id=school_id
    )


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = CommsWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure session (purpose + channels)
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    purpose = (request.data.get("purpose") or "").strip()
    if not purpose:
        return Response({"error": "purpose is required"}, status=status.HTTP_400_BAD_REQUEST)
    if len(purpose) > 128:
        return Response({"error": "purpose must be 128 characters or fewer"}, status=status.HTTP_400_BAD_REQUEST)

    channels_raw = request.data.get("channels")
    if not isinstance(channels_raw, list) or len(channels_raw) == 0:
        return Response({"error": "channels must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    invalid = [c for c in channels_raw if c not in CommsWizardSession.VALID_CHANNELS]
    if invalid:
        return Response(
            {"error": f"Invalid channels: {invalid}. Valid: {sorted(CommsWizardSession.VALID_CHANNELS)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    channels = list(dict.fromkeys(channels_raw))  # deduplicate preserving order

    session.purpose = purpose
    session.channels = channels
    session.status = CommsWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "purpose": purpose, "channels": channels})


# ---------------------------------------------------------------------------
# 3. Draft message (subject + body)
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def draft_message(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        CommsWizardSession.STATUS_CONFIGURED,
        CommsWizardSession.STATUS_MESSAGE_DRAFTED,
    ):
        return Response(
            {"error": f"Cannot draft message from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    subject = (request.data.get("subject") or "").strip()
    if not subject:
        return Response({"error": "subject is required"}, status=status.HTTP_400_BAD_REQUEST)
    if len(subject) > 255:
        return Response({"error": "subject must be 255 characters or fewer"}, status=status.HTTP_400_BAD_REQUEST)

    body = (request.data.get("body") or "").strip()
    if not body:
        return Response({"error": "body is required"}, status=status.HTTP_400_BAD_REQUEST)

    session.subject = subject
    session.body = body
    session.status = CommsWizardSession.STATUS_MESSAGE_DRAFTED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "subject": subject,
    })


# ---------------------------------------------------------------------------
# 4. Stage recipients
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_recipients(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        CommsWizardSession.STATUS_MESSAGE_DRAFTED,
        CommsWizardSession.STATUS_RECIPIENTS_STAGED,
    ):
        return Response(
            {"error": f"Cannot stage recipients from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    recipients_raw = request.data.get("recipients")
    if not isinstance(recipients_raw, list):
        return Response({"error": "recipients must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    if len(recipients_raw) == 0:
        return Response({"error": "At least one recipient is required"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    normalised = []
    seen_tos = set()
    for i, r in enumerate(recipients_raw):
        prefix = f"recipients[{i}]"
        if not isinstance(r, dict):
            errors.append(f"{prefix}: must be an object")
            continue
        to = (r.get("to") or "").strip()
        if not to:
            errors.append(f"{prefix}: 'to' is required")
            continue
        if to in seen_tos:
            errors.append(f"{prefix}: duplicate recipient '{to}'")
            continue
        seen_tos.add(to)
        normalised.append({"to": to, "name": (r.get("name") or "").strip()})

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.recipients = normalised
    session.status = CommsWizardSession.STATUS_RECIPIENTS_STAGED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "recipients_count": len(normalised),
    })


# ---------------------------------------------------------------------------
# 5. Commit — write OutboxMessage records
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    # Idempotency guard
    if session.status == CommsWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **session.commit_result})

    if session.status != CommsWizardSession.STATUS_RECIPIENTS_STAGED:
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)

    messages_created = 0
    messages_skipped = 0

    with transaction.atomic():
        for recipient in session.recipients:
            for channel in session.channels:
                ikey = f"comms-wizard:{session.id}:{channel}:{recipient['to']}"
                _, created = OutboxMessage.objects.get_or_create(
                    idempotency_key=ikey,
                    defaults={
                        "school_id": str(school_id),
                        "channel": channel.upper(),
                        "to": recipient["to"],
                        "subject": session.subject,
                        "body": session.body,
                        "status": OutboxMessage.STATUS_PENDING,
                    },
                )
                if created:
                    messages_created += 1
                else:
                    messages_skipped += 1

    commit_result = {
        "messages_created": messages_created,
        "messages_skipped": messages_skipped,
    }
    session.commit_result = commit_result
    session.status = CommsWizardSession.STATUS_COMMITTED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **commit_result,
    })


# ---------------------------------------------------------------------------
# 6. Verify
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == CommsWizardSession.STATUS_VERIFIED:
        return Response({
            "session_id": str(session.id),
            "status": session.status,
            **session.commit_result,
        })

    if session.status != CommsWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    session.status = CommsWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **session.commit_result,
    })
