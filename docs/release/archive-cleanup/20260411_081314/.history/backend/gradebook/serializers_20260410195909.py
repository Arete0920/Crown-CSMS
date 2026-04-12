from rest_framework import serializers

from .models import GradeEntry


class AssignmentSerializer(serializers.Serializer):
    """FK-backed assignment data from academics.Assignment."""
    assignment_id = serializers.UUIDField()
    assignment_name = serializers.CharField()
    points_possible = serializers.DecimalField(
        max_digits=6,
        decimal_places=2,
        required=False,
        allow_null=True,
    )


class GradebookAssignmentSerializer(serializers.Serializer):
    """FK-backed assignment data from academics.Assignment."""
    assignment_id = serializers.UUIDField(allow_null=True)
    assignment_name = serializers.CharField(allow_blank=True, allow_null=True)
    points_possible = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)


class GradebookStudentSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student__first_name = serializers.CharField()
    student__last_name = serializers.CharField()


class GradebookRosterStudentSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    grade_level = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class GradebookSectionRosterResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    students = GradebookRosterStudentSerializer(many=True)


class GradebookSectionSummaryResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    student_count = serializers.IntegerField()
    assignment_count = serializers.IntegerField()
    missing_count = serializers.IntegerField()
    class_average_pct = serializers.FloatField(allow_null=True)
    last_updated = serializers.DateTimeField(allow_null=True)


class GradebookGradeRowStudentSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    grade_level = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class GradebookSectionGradeRowSerializer(serializers.Serializer):
    student = GradebookGradeRowStudentSerializer()
    scores = serializers.DictField(child=serializers.JSONField())


class GradebookSectionGradesResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    course_code = serializers.CharField(allow_blank=True, allow_null=True)
    course_name = serializers.CharField(allow_blank=True, allow_null=True)
    term_code = serializers.CharField(allow_blank=True, allow_null=True)
    assignments = GradebookAssignmentSerializer(many=True)
    rows = GradebookSectionGradeRowSerializer(many=True)


class GradebookDrilldownRowSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    grade_level = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    category_id = serializers.CharField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
    total_points_earned = serializers.FloatField()
    total_points_possible = serializers.FloatField()
    pct = serializers.FloatField()
    status = serializers.CharField()
    assignments_count = serializers.IntegerField()
    missing_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    last_submission = serializers.DateTimeField(allow_null=True)


class GradebookSectionDrilldownResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    section_name = serializers.CharField(allow_blank=True)
    total = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    rows = GradebookDrilldownRowSerializer(many=True)


class GradebookBulkUpsertItemSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    points_earned = serializers.DecimalField(max_digits=8, decimal_places=2, allow_null=True)


class GradebookBulkUpsertRequestSerializer(serializers.Serializer):
    grades = GradebookBulkUpsertItemSerializer(many=True)


class GradebookBulkUpsertRowSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    assignment_id = serializers.UUIDField()
    points_earned = serializers.CharField(allow_null=True)


class GradebookBulkUpsertResponseSerializer(serializers.Serializer):
    created = serializers.IntegerField()
    updated = serializers.IntegerField()
    count = serializers.IntegerField()
    rows = GradebookBulkUpsertRowSerializer(many=True)


class GradebookParentAssignmentSerializer(serializers.Serializer):
    assignment_name = serializers.CharField()
    points_possible = serializers.CharField()
    points_earned = serializers.CharField(allow_null=True)
    percentage = serializers.FloatField(allow_null=True)
    date_assigned = serializers.DateTimeField(allow_null=True)


class GradebookParentCourseSerializer(serializers.Serializer):
    course_code = serializers.CharField()
    course_name = serializers.CharField()
    section_id = serializers.UUIDField()
    term = serializers.CharField(allow_blank=True, allow_null=True)
    overall_percentage = serializers.FloatField(allow_null=True)
    letter_grade = serializers.CharField(allow_null=True)
    total_points_possible = serializers.FloatField()
    total_points_earned = serializers.FloatField()
    assignments_count = serializers.IntegerField()
    assignments = GradebookParentAssignmentSerializer(many=True)


class GradebookParentStudentGradesSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    grade_level = serializers.CharField(allow_blank=True, allow_null=True)
    courses = GradebookParentCourseSerializer(many=True)


class GradeEntryUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GradeEntry
        fields = ["points_earned"]
