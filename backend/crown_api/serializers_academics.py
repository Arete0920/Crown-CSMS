from rest_framework import serializers

from crown_api.models import AttendanceRecord, Course, GradeRecord


class CourseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = (
            "course_code",
            "name",
            "term",
        )


class AttendanceRecordReadSerializer(serializers.ModelSerializer):
    attendance_id = serializers.UUIDField(source="id", read_only=True)
    course = CourseMiniSerializer(read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = (
            "attendance_id",
            "date",
            "status",
            "minutes_late",
            "notes_public",
            "course",
        )


class GradeRecordReadSerializer(serializers.ModelSerializer):
    grade_id = serializers.UUIDField(source="id", read_only=True)
    course = CourseMiniSerializer(read_only=True)

    class Meta:
        model = GradeRecord
        fields = (
            "grade_id",
            "period",
            "assignment_name",
            "category",
            "score",
            "score_max",
            "letter_grade",
            "posted_at",
            "notes_public",
            "course",
        )
