from rest_framework import serializers


class AssignmentSerializer(serializers.Serializer):
    assignment_name = serializers.CharField()
    points_possible = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)


class GradebookAssignmentSerializer(serializers.Serializer):
    assignment_name = serializers.CharField()
    points_possible = serializers.DecimalField(max_digits=8, decimal_places=2)


class GradebookStudentSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student__first_name = serializers.CharField()
    student__last_name = serializers.CharField()
