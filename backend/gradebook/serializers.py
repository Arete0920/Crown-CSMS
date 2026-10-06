from rest_framework import serializers
from .models import GradeEntry


class AssignmentSerializer(serializers.Serializer):
    """FK-backed assignment data from academics.Assignment."""
    assignment_id = serializers.UUIDField(allow_null=True)
    assignment_name = serializers.CharField()
    points_possible = serializers.DecimalField(max_digits=6, decimal_places=2, required=False)


class GradebookAssignmentSerializer(serializers.Serializer):
    """FK-backed assignment data from academics.Assignment."""
    assignment_id = serializers.UUIDField(allow_null=True)
    assignment_name = serializers.CharField()
    points_possible = serializers.DecimalField(max_digits=8, decimal_places=2)


class GradebookStudentSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student__first_name = serializers.CharField()
    student__last_name = serializers.CharField()


class GradeEntryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeEntry
        fields = ["points_earned"]



class SectionRosterResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    students = serializers.ListField(child=serializers.DictField())


class SectionAssignmentsResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    assignments = GradebookAssignmentSerializer(many=True)


class SectionSummaryResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    student_count = serializers.IntegerField()
    assignment_count = serializers.IntegerField()
    missing_count = serializers.IntegerField()
    class_average_pct = serializers.FloatField(allow_null=True)
    last_updated = serializers.DateTimeField(allow_null=True)


class SectionGradesResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    term_code = serializers.CharField()
    assignments = GradebookAssignmentSerializer(many=True)
    rows = serializers.ListField(child=serializers.DictField())


class GradebookDrilldownRowSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    grade_level = serializers.CharField(allow_blank=True)
    category_id = serializers.UUIDField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
    total_points_earned = serializers.FloatField()
    total_points_possible = serializers.FloatField()
    pct = serializers.FloatField()
    status = serializers.ChoiceField(choices=["normal", "missing", "below_threshold"])
    assignments_count = serializers.IntegerField()
    missing_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    last_submission = serializers.DateTimeField(allow_null=True)


class SectionDrilldownResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    section_name = serializers.CharField(allow_blank=True)
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    rows = GradebookDrilldownRowSerializer(many=True)
