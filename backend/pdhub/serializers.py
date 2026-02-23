from rest_framework import serializers
from .models import PDResource, PDSession


class PDResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDResource
        fields = "__all__"


class PDSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PDSession
        fields = "__all__"
