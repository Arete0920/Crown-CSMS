from django.conf import settings as django_settings
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .graph_client import GraphClient
from .models import M365WebhookEvent


def _get_document_models():
    from documents.models import DocumentPacket, DocumentStatus, DocumentTimelineEvent

    return DocumentPacket, DocumentStatus, DocumentTimelineEvent


class WorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = request.headers.get("X-School-Id")

        try:
            DocumentPacket, DocumentStatus, _ = _get_document_models()
        except Exception:
            return Response(
                {
                    "counts": {
                        "needs_review": 0,
                        "awaiting_signature": 0,
                        "partially_signed": 0,
                        "rejected": 0,
                    },
                    "queue": [],
                }
            )

        packets = DocumentPacket.objects.filter(school_id=school_id) if school_id else DocumentPacket.objects.none()
        return Response(
            {
                "counts": {
                    "needs_review": packets.filter(status=DocumentStatus.NEEDS_REVIEW).count(),
                    "awaiting_signature": packets.filter(status=DocumentStatus.AWAITING_SIGNATURE).count(),
                    "partially_signed": packets.filter(status=DocumentStatus.PARTIALLY_SIGNED).count(),
                    "rejected": packets.filter(status=DocumentStatus.REJECTED).count(),
                },
                "queue": list(
                    packets.order_by("-updated_at").values("id", "title", "workflow_context", "status", "updated_at")[:10]
                ),
            }
        )


class ServicesStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = request.headers.get("X-School-Id")
        client = GraphClient(school_id)
        graph_configured = bool(client.tenant_id and client.client_id and client.client_secret)
        outlook_configured = bool(graph_configured and getattr(django_settings, "GRAPH_FROM_USER", "").strip())
        sharepoint_configured = bool(graph_configured and (client.site_id or client.drive_id))

        return Response(
            {
                "teams": graph_configured,
                "outlook": outlook_configured,
                "sharepoint": sharepoint_configured,
                "planner": graph_configured,
                "esignature": True,
            }
        )


class FlowCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.data
        school_id = payload.get("school_id")
        packet_id = payload.get("packet_id")
        event_type = payload.get("event_type", "flow_update")
        event = None
        try:
            event = M365WebhookEvent.objects.create(
                school_id=school_id,
                packet_id=packet_id,
                event_type=event_type,
                payload=payload,
            )
        except Exception:
            event = None

        if packet_id:
            try:
                DocumentPacket, DocumentStatus, DocumentTimelineEvent = _get_document_models()
            except Exception:
                DocumentPacket = DocumentStatus = DocumentTimelineEvent = None

            if DocumentPacket and DocumentStatus and DocumentTimelineEvent:
                packet = DocumentPacket.objects.filter(id=packet_id, school_id=school_id).first()
                if packet:
                    mapped_status = payload.get("mapped_status")
                    if mapped_status in dict(DocumentStatus.choices):
                        packet.status = mapped_status
                        packet.save(update_fields=["status", "updated_at"])
                    DocumentTimelineEvent.objects.create(
                        packet=packet,
                        school_id=packet.school_id,
                        event_type=event_type,
                        source_system="power_automate",
                        metadata=payload,
                    )

        if event is not None:
            event.processed = True
            event.save(update_fields=["processed"])
        return Response({"ok": True})


class SharePointDeeplinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = request.headers.get("X-School-Id")
        folder_path = request.query_params.get("folder", "")
        client = GraphClient(school_id)
        return Response({"url": client.sharepoint_deeplink(folder_path)})


class TeamsDeeplinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        team_hint = request.query_params.get("team", "general")
        return Response({"url": f"https://teams.microsoft.com/l/channel/{team_hint}"})
