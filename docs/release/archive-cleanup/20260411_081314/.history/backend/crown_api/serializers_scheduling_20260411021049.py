from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from crown_api.models import Person, SectionEnrollment, Term


class TermMiniSerializer(serializers.ModelSerializer):
    term_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Term
        fields = (
            "term_id",
            "code",
            "name",
        )


class CourseMiniSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()

    class Meta:
        ref_name = "SchedulingCourseMini"


class TeacherMiniSerializer(serializers.ModelSerializer):
    person_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Person
        fields = (
            "person_id",
            "first_name",
            "last_name",
        )


class StudentScheduleEnrollmentSerializer(serializers.ModelSerializer):
    term = TermMiniSerializer(source="section.term", read_only=True)
    course = serializers.SerializerMethodField()
    teacher = TeacherMiniSerializer(source="section.teacher", read_only=True)

    section_code = serializers.CharField(source="section.section_code", read_only=True)
    room = serializers.CharField(source="section.room", read_only=True)
    meeting_days = serializers.CharField(source="section.meeting_days", read_only=True)
    meeting_time = serializers.CharField(source="section.meeting_time", read_only=True)

    class Meta:
        model = SectionEnrollment
        fields = (
            "term",
            "course",
            "section_code",
            "teacher",
            "room",
            "meeting_days",
            "meeting_time",
        )

    @extend_schema_field(CourseMiniSerializer)
    def get_course(self, obj):
        course = getattr(getattr(obj, "section", None), "course", None)
        if not course:
            return None
        return {"code": course.course_code, "name": course.name}


class TermListSerializer(serializers.ModelSerializer):
    term_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Term
        fields = (
            "term_id",
            "code",
            "name",
            "start_date",
            "end_date",
            "active",
        )


class SchedulingSectionListSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    term = TermMiniSerializer()
    course = CourseMiniSerializer()
    section_code = serializers.CharField()
    name = serializers.CharField()
    teacher = TeacherMiniSerializer(allow_null=True)
    room = serializers.CharField()
    meeting_days = serializers.CharField()
    meeting_time = serializers.CharField()
