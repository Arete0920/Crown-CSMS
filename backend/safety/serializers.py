from rest_framework import serializers
from .models import IncidentReport


class IncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IncidentReport
        fields = "__all__"
