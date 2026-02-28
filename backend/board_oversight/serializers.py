from rest_framework import serializers
from .models import BoardPacket, BoardReportSnapshot


class BoardReportSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = BoardReportSnapshot
        fields = ["id", "school_id", "as_of_date", "period_label", "payload", "created_at"]


class BoardPacketSerializer(serializers.ModelSerializer):
    snapshots = BoardReportSnapshotSerializer(many=True, read_only=True)

    class Meta:
        model = BoardPacket
        fields = ["id", "school_id", "title", "meeting_date", "description", "snapshots", "documents", "created_at"]
