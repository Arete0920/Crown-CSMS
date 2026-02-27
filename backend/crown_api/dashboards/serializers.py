"""
Dashboard API serializers — stable contract for Me / Summary / Drilldown / Alerts.
"""
from rest_framework import serializers


class DashboardMeSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    display_name = serializers.CharField()
    roles = serializers.ListField(child=serializers.CharField())
    default_route = serializers.CharField()
    features = serializers.DictField(child=serializers.BooleanField(), required=False)


class DrilldownConfigSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    endpoint = serializers.CharField()


class DashboardWidgetSerializer(serializers.Serializer):
    key = serializers.CharField()
    type = serializers.ChoiceField(choices=["stat", "chart_line", "chart_donut", "table", "feed", "flip", "actions"])
    title = serializers.CharField()
    subtitle = serializers.CharField(required=False, allow_blank=True)
    size = serializers.ChoiceField(choices=["sm", "md", "lg"])
    priority = serializers.IntegerField()
    data = serializers.JSONField()
    drilldown = DrilldownConfigSerializer(required=False)


class DashboardSummarySerializer(serializers.Serializer):
    role = serializers.CharField()
    school_id = serializers.CharField()
    generated_at = serializers.CharField()  # ISO string — already formatted
    widgets = DashboardWidgetSerializer(many=True)


class DashboardAlertSerializer(serializers.Serializer):
    key = serializers.CharField()
    level = serializers.ChoiceField(choices=["good", "warn", "bad", "info"])
    text = serializers.CharField()
    action_url = serializers.CharField(required=False, allow_blank=True)
    widget = serializers.CharField(required=False, allow_blank=True)


class DashboardAlertsResponseSerializer(serializers.Serializer):
    school_id = serializers.CharField()
    generated_at = serializers.CharField()
    alerts = DashboardAlertSerializer(many=True)
