from __future__ import annotations

import logging
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from django.contrib.auth import get_user_model
from core.models import School

from crown_api.models_comms_core import MessageThread, Message
from comms.api.serializers import (
    ThreadListSerializer,
    ThreadDetailSerializer,
    ComposeThreadSerializer,
)

logger = logging.getLogger(__name__)

def _get_school_from_request(request):
    school = getattr(request, "school", None)
    if school:
        return school
    school_id = request.headers.get("X-School-Id")
    if not school_id:
        return None
    try:
        return School.objects.get(pk=school_id)
    except School.DoesNotExist:
        return None

def _thread_qs_for_school(school):
    # Some projects store school as FK, some as UUID field.
    # We try both patterns safely.
    qs = MessageThread.objects.order_by("-created_at")
    if hasattr(MessageThread, "school"):
        return qs.filter(school=school)
    if hasattr(MessageThread, "school_id"):
        return qs.filter(school_id=str(school.id))
    # Fail closed: no school field means we cannot safely scope
    return qs.none()

class ThreadsList(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        qs = _thread_qs_for_school(school).order_by("-created_at")[:500]
        return Response(ThreadListSerializer(qs, many=True).data)

class ThreadDetail(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, thread_id):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        try:
            t = _thread_qs_for_school(school).get(id=thread_id)
        except MessageThread.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)

        return Response(ThreadDetailSerializer(t).data)

class ThreadPostMessage(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, thread_id):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        try:
            t = _thread_qs_for_school(school).get(id=thread_id)
        except MessageThread.DoesNotExist:
            return Response({"detail":"Not found"}, status=404)

        body = (request.data or {}).get("body","").strip()
        if not body:
            return Response({"detail":"body required"}, status=400)

        msg = Message.objects.create(
            thread=t,
            sender=request.user,
            body=body,
        )
        return Response({"ok": True, "message_id": str(msg.id)}, status=201)

class ComposeThread(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        ser = ComposeThreadSerializer(data=request.data or {})
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        # Create thread (school-scoped where possible)
        kwargs = {"subject": d["subject"]}
        if hasattr(MessageThread, "school"):
            kwargs["school"] = school
        elif hasattr(MessageThread, "school_id"):
            kwargs["school_id"] = str(school.id)

        t = MessageThread.objects.create(**kwargs)

        Message.objects.create(
            thread=t,
            sender=request.user,
            body=d["body"],
        )

        # Optional recipients concept: if model supports participants, try attach
        # (safe no-op if not)
        recips = d.get("recipients") or []
        if recips:
            User = get_user_model()
            users = list(User.objects.filter(id__in=recips)[:50])

            # common patterns: participants m2m
            if hasattr(t, "participants"):
                try:
                    t.participants.add(*users)
                except Exception:
                    logger.debug("participants.add failed — non-critical", exc_info=True)

        return Response({"ok": True, "thread_id": str(t.id)}, status=201)


# ---------------------------------------------------------------------------
# Outbox smoke-test endpoint
# ---------------------------------------------------------------------------

class SendTestEmail(APIView):
    """
    POST /api/comms/send-test-email/

    Enqueues a test email through the outbox so the full pipeline can be
    verified without hitting production workloads.

    Request body (JSON):
        to        — recipient email address (required)
        subject   — email subject            (optional)
        body      — HTML email body          (optional)
        school_id — tenant UUID              (optional, defaults to smoke-test sentinel)

    Returns the outbox message ID for tracing in the Django admin panel.
    Requires authentication.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from comms.outbox_service import enqueue_email  # local import to keep view thin

        data      = request.data or {}
        to        = (data.get("to") or "").strip()
        subject   = (data.get("subject") or "Crown2026 Test Email").strip()
        body      = (data.get("body") or "<p>Crown2026 outbox smoke test — if you see this, Graph delivery works.</p>").strip()
        school_id = (data.get("school_id") or "smoke-test").strip()

        if not to:
            return Response({"error": "Field 'to' is required."}, status=status.HTTP_400_BAD_REQUEST)

        msg = enqueue_email(
            school_id=school_id,
            to=to,
            subject=subject,
            body_html=body,
        )

        return Response(
            {
                "status":     "queued",
                "message_id": str(msg.id),
                "channel":    msg.channel,
                "to":         msg.to,
                "subject":    msg.subject,
            },
            status=status.HTTP_202_ACCEPTED,
        )
