from django.conf import settings as django_settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .graph_client import GraphClient
from .models import M365WebhookEvent


def _get_document_models():
    from documents.models import DocumentPacket, DocumentStatus, DocumentTimelineEvent

    return DocumentPacket, DocumentStatus, DocumentTimelineEvent


M365WorkspaceSerializer = inline_serializer(
    name="M365WorkspaceSerializer",
    fields={
        "counts": inline_serializer(
            name="M365WorkspaceCountsSerializer",
            fields={
                "needs_review": serializers.IntegerField(),
                "awaiting_signature": serializers.IntegerField(),
                "partially_signed": serializers.IntegerField(),
                "rejected": serializers.IntegerField(),
            },
        ),
        "queue": serializers.ListField(child=serializers.DictField()),
    },
)
M365ServicesStatusSerializer = inline_serializer(
    name="M365ServicesStatusSerializer",
    fields={
        "teams": serializers.BooleanField(),
        "outlook": serializers.BooleanField(),
        "sharepoint": serializers.BooleanField(),
        "planner": serializers.BooleanField(),
        "esignature": serializers.BooleanField(),
    },
)
M365FlowCallbackRequestSerializer = inline_serializer(
    name="M365FlowCallbackRequestSerializer",
    fields={
        "school_id": serializers.CharField(required=False, allow_blank=True),
        "packet_id": serializers.CharField(required=False, allow_blank=True),
        "event_type": serializers.CharField(required=False, allow_blank=True),
        "mapped_status": serializers.CharField(required=False, allow_blank=True),
        "payload": serializers.DictField(required=False),
    },
)
M365OkSerializer = inline_serializer(name="M365OkSerializer", fields={"ok": serializers.BooleanField()})
M365UrlSerializer = inline_serializer(name="M365UrlSerializer", fields={"url": serializers.CharField()})


class WorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="m365_workspace", responses=M365WorkspaceSerializer)
    def get(self, request):
        school_id = request.headers.get("X-School-Id")

        try:
            document_packet_model, document_status, _ = _get_document_models()
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

        packets = (
            document_packet_model._default_manager.filter(school_id=school_id)
            if school_id
            else document_packet_model._default_manager.none()
        )
        return Response(
            {
                "counts": {
                    "needs_review": packets.filter(status=document_status.NEEDS_REVIEW).count(),
                    "awaiting_signature": packets.filter(status=document_status.AWAITING_SIGNATURE).count(),
                    "partially_signed": packets.filter(status=document_status.PARTIALLY_SIGNED).count(),
                    "rejected": packets.filter(status=document_status.REJECTED).count(),
                },
                "queue": list(
                    packets.order_by("-updated_at").values("id", "title", "workflow_context", "status", "updated_at")[:10]
                ),
            }
        )


class ServicesStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="m365_services_status", responses=M365ServicesStatusSerializer)
    def get(self, request):
        school_id = request.headers.get("X-School-Id")
        client = GraphClient(school_id)
        graph_configured = bool(client.tenant_id and client.client_id and client.client_secret)
        outlook_configured = bool(graph_configured and getattr(django_settings, "GRAPH_FROM_USER", "").strip())
        sharepoint_configured = bool(graph_configured and (client.site_id or client.drive_id))

        try:
            _get_document_models()
            esignature_configured = True
        except Exception:
            esignature_configured = False

        return Response(
            {
                "teams": graph_configured,
                "outlook": outlook_configured,
                "sharepoint": sharepoint_configured,
                "planner": graph_configured,
                "esignature": esignature_configured,
            }
        )


class FlowCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        operation_id="m365_flow_callback",
        request=M365FlowCallbackRequestSerializer,
        responses=M365OkSerializer,
    )
    def post(self, request):
        payload = request.data
        school_id = payload.get("school_id")
        packet_id = payload.get("packet_id")
        event_type = payload.get("event_type", "flow_update")
        event = None
        try:
            event = M365WebhookEvent._default_manager.create(
                school_id=school_id,
                packet_id=packet_id,
                event_type=event_type,
                payload=payload,
            )
        except Exception:
            event = None

        if packet_id:
            try:
                document_packet_model, document_status, document_timeline_event_model = _get_document_models()
            except Exception:
                document_packet_model = document_status = document_timeline_event_model = None

            if document_packet_model and document_status and document_timeline_event_model:
                packet = document_packet_model._default_manager.filter(id=packet_id, school_id=school_id).first()
                if packet:
                    mapped_status = payload.get("mapped_status")
                    if mapped_status in dict(document_status.choices):
                        packet.status = mapped_status
                        packet.save(update_fields=["status", "updated_at"])
                    document_timeline_event_model._default_manager.create(
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

    @extend_schema(operation_id="m365_sharepoint_deeplink", responses=M365UrlSerializer)
    def get(self, request):
        school_id = request.headers.get("X-School-Id")
        folder_path = request.query_params.get("folder", "")
        client = GraphClient(school_id)
        return Response({"url": client.sharepoint_deeplink(folder_path)})


class TeamsDeeplinkView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="m365_teams_deeplink", responses=M365UrlSerializer)
    def get(self, request):
        team_hint = request.query_params.get("team", "general")
        return Response({"url": f"https://teams.microsoft.com/l/channel/{team_hint}"})
