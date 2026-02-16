from rest_framework import serializers
from .models import (
    Classroom,
    ClassroomEnrollment,
    ClassroomAnnouncement,
    ClassroomAssignment,
    ClassroomSeatingChart,
)


class ClassroomListSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.SerializerMethodField()
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Classroom
        fields = [
            "id",
            "name",
            "room",
            "grade_level",
            "is_active",
            "homeroom_teacher_name",
            "student_count",
        ]

    def get_homeroom_teacher_name(self, obj):
        if not obj.homeroom_teacher_id:
            return ""
        # Staff likely has first_name/last_name or display_name; be defensive.
        fn = getattr(obj.homeroom_teacher, "first_name", "") or ""
        ln = getattr(obj.homeroom_teacher, "last_name", "") or ""
        name = (fn + " " + ln).strip()
        return name or str(obj.homeroom_teacher)


class ClassroomEnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = ClassroomEnrollment
        fields = ["id", "student", "student_name", "created_at"]

    def get_student_name(self, obj):
        s = obj.student
        # Defensive: Student might have different naming fields.
        fn = getattr(s, "first_name", "") or ""
        ln = getattr(s, "last_name", "") or ""
        full = (fn + " " + ln).strip()
        return full or getattr(s, "full_name", "") or str(s)


class ClassroomAnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomAnnouncement
        fields = ["id", "title", "body", "pinned", "created_at"]


class ClassroomAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomAssignment
        fields = ["id", "title", "description", "due_date", "points", "status", "created_at"]


class ClassroomSeatingChartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassroomSeatingChart
        fields = ["id", "layout", "updated_at"]


class ClassroomDetailSerializer(serializers.ModelSerializer):
    homeroom_teacher_name = serializers.SerializerMethodField()
    students = serializers.SerializerMethodField()
    announcements = ClassroomAnnouncementSerializer(many=True, read_only=True)
    assignments = ClassroomAssignmentSerializer(many=True, read_only=True)
    seating_chart = ClassroomSeatingChartSerializer(read_only=True)

    class Meta:
        model = Classroom
        fields = [
            "id",
            "name",
            "room",
            "grade_level",
            "is_active",
            "homeroom_teacher_name",
            "students",
            "announcements",
            "assignments",
            "seating_chart",
        ]

    def get_homeroom_teacher_name(self, obj):
        if not obj.homeroom_teacher_id:
            return ""
        fn = getattr(obj.homeroom_teacher, "first_name", "") or ""
        ln = getattr(obj.homeroom_teacher, "last_name", "") or ""
        name = (fn + " " + ln).strip()
        return name or str(obj.homeroom_teacher)

    def get_students(self, obj):
        enrollments = obj.enrollments.select_related("student").all().order_by("created_at")
        out = []
        for e in enrollments:
            s = e.student
            fn = getattr(s, "first_name", "") or ""
            ln = getattr(s, "last_name", "") or ""
            full = (fn + " " + ln).strip()
            out.append({"id": str(getattr(s, "id")), "name": full or str(s)})
        return out
