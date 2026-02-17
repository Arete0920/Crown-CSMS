from __future__ import annotations
from rest_framework import serializers

# Existing comms core models live here (per earlier scan)
from crown_api.models_comms_core import MessageThread, Message

class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "thread", "sender_name", "body", "created_at"]

    def get_sender_name(self, obj):
        u = getattr(obj, "sender", None)
        if not u:
            return None
        try:
            name = u.get_full_name()
        except Exception:
            name = None
        return name or str(u)

class ThreadListSerializer(serializers.ModelSerializer):
    last_message_preview = serializers.SerializerMethodField()
    last_message_at = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ["id", "subject", "created_at", "last_message_at", "last_message_preview"]

    def get_last_message_preview(self, obj):
        m = getattr(obj, "messages", None)
        if m is None:
            return ""
        last = m.order_by("-created_at").first()
        if not last:
            return ""
        body = getattr(last, "body", "") or ""
        return body[:120]

    def get_last_message_at(self, obj):
        m = getattr(obj, "messages", None)
        if m is None:
            return None
        last = m.order_by("-created_at").first()
        return getattr(last, "created_at", None)

class ThreadDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = MessageThread
        fields = ["id", "subject", "created_at", "messages"]

    def get_messages(self, obj):
        qs = obj.messages.order_by("created_at")[:500]
        return MessageSerializer(qs, many=True).data

class ComposeThreadSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=180)
    body = serializers.CharField()
    # Minimal recipient concept for demo: optional list of user UUIDs
    recipients = serializers.ListField(child=serializers.UUIDField(), required=False)
