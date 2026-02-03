from rest_framework import serializers


class AssignmentSerializer(serializers.Serializer):
    assignment_name = serializers.CharField()
    points_possible = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)
