# curricula/serializers.py
from rest_framework import serializers
from .models import CurriculumMap, Unit, Lesson


class CurriculumMapSerializer(serializers.ModelSerializer):
    curriculum_map_id = serializers.UUIDField(source="id", read_only=True)
    course_id = serializers.UUIDField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)

    class Meta:
        model = CurriculumMap
        fields = [
            "curriculum_map_id",
            "school_id",
            "course_id",
            "course_code",
            "course_name",
            "title",
            "description",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class UnitSerializer(serializers.ModelSerializer):
    unit_id = serializers.UUIDField(source="id", read_only=True)
    curriculum_map_id = serializers.UUIDField(read_only=True)
    curriculum_map_title = serializers.CharField(source="curriculum_map.title", read_only=True)

    class Meta:
        model = Unit
        fields = [
            "unit_id",
            "school_id",
            "curriculum_map_id",
            "curriculum_map_title",
            "sequence",
            "title",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]


class LessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="id", read_only=True)
    unit_id = serializers.UUIDField(read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "lesson_id",
            "school_id",
            "unit_id",
            "unit_title",
            "sequence",
            "title",
            "description",
            "objectives",
            "resources",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
