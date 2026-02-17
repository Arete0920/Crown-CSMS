from __future__ import annotations
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from integrations.models import TeamsPreviewAudit
from core.models import School

def _get_school_from_request(request):
    school = getattr(request, "school", None)
    if school:
        return school
    school_id = request.headers.get("X-School-Id")
    if not school_id:
        return None
    try:
        return School.objects.get(id=school_id)
    except School.DoesNotExist:
        return None

class TeamsPreview(APIView):
    """
    Demo-only integration seam. No outbound calls.
    Returns the message card payload that WOULD be sent to Teams.
    Also writes to TeamsPreviewAudit for demo credibility.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        school = _get_school_from_request(request)
        if not school:
            return Response({"detail":"Missing or invalid school context"}, status=400)

        body = request.data or {}
        event_type = body.get("event_type","unknown")
        title = body.get("title","Crown Notification")
        text = body.get("text","")
        channel = body.get("channel","staff-general")

        payload = {
            "target": "microsoft_teams",
            "channel": channel,
            "title": title,
            "text": text,
            "source": "crown2026",
            "demo_mode": True,
        }

        TeamsPreviewAudit.objects.create(school=school, event_type=event_type, payload=payload)
        return Response({"queued": True, "payload": payload}, status=200)
