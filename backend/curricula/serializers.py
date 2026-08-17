from rest_framework import serializers

from academics.models import Course
from households.scoping import get_request_school_id

from .models import (
    CurriculumMap,
    CurriculumMapVersion,
    CurriculumMapVersionEvent,
    Lesson,
    Unit,
)


def _request_school_id(serializer):
    request = serializer.context.get("request")
    if request is None:
        return ""
    school_id = get_request_school_id(request)
    return str(school_id) if school_id else ""


def _scope_relation_field(serializer, field_name, model):
    school_id = _request_school_id(serializer)
    serializer.fields[field_name].queryset = (
        model.objects.filter(school_id=school_id) if school_id else model.objects.none()
    )


class CurriculumMapSerializer(serializers.ModelSerializer):
    curriculum_map_id = serializers.UUIDField(source="id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    course_id = serializers.PrimaryKeyRelatedField(
        source="course",
        queryset=Course.objects.none(),
        required=False,
        allow_null=True,
    )
    course_code = serializers.CharField(source="course.code", read_only=True, allow_null=True)
    course_name = serializers.CharField(source="course.name", read_only=True, allow_null=True)
    published_version_id = serializers.SerializerMethodField()

    class Meta:
        model = CurriculumMap
        fields = ["curriculum_map_id", "school_id", "course_id", "course_code", "course_name", "title", "description", "grade_band", "subject", "active", "published_version_id", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _scope_relation_field(self, "course_id", Course)

    def validate_course_id(self, course):
        request_school_id = _request_school_id(self)
        if course is not None and request_school_id and str(course.school_id) != request_school_id:
            raise serializers.ValidationError("Course must belong to the current school.")
        return course

    def get_published_version_id(self, obj):
        version = obj.versions.filter(status=CurriculumMapVersion.Status.PUBLISHED).only("id").first()
        return str(version.id) if version else None


class CurriculumMapVersionEventSerializer(serializers.ModelSerializer):
    event_id = serializers.UUIDField(source="id", read_only=True)
    actor_id = serializers.UUIDField(source="actor.id", read_only=True, allow_null=True)

    class Meta:
        model = CurriculumMapVersionEvent
        fields = ["event_id", "from_status", "to_status", "actor_id", "notes", "created_at"]
        read_only_fields = fields


class CurriculumMapVersionSerializer(serializers.ModelSerializer):
    curriculum_version_id = serializers.UUIDField(source="id", read_only=True)
    curriculum_map_id = serializers.UUIDField(source="curriculum_map.id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    submitted_by_id = serializers.UUIDField(source="submitted_by.id", read_only=True, allow_null=True)
    approved_by_id = serializers.UUIDField(source="approved_by.id", read_only=True, allow_null=True)
    unit_count = serializers.SerializerMethodField()
    lesson_count = serializers.SerializerMethodField()
    events = CurriculumMapVersionEventSerializer(many=True, read_only=True)

    class Meta:
        model = CurriculumMapVersion
        fields = ["curriculum_version_id", "curriculum_map_id", "school_id", "version_number", "status", "change_summary", "effective_from", "effective_to", "submitted_by_id", "submitted_at", "approved_by_id", "approved_at", "published_at", "retired_at", "unit_count", "lesson_count", "events", "created_at", "updated_at"]
        read_only_fields = fields

    def get_unit_count(self, obj):
        return obj.units.count()

    def get_lesson_count(self, obj):
        return Lesson.objects.filter(unit__curriculum_version=obj).count()


class UnitSerializer(serializers.ModelSerializer):
    unit_id = serializers.UUIDField(source="id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    curriculum_map_id = serializers.PrimaryKeyRelatedField(source="curriculum_map", queryset=CurriculumMap.objects.none())
    curriculum_version_id = serializers.PrimaryKeyRelatedField(source="curriculum_version", queryset=CurriculumMapVersion.objects.none())
    curriculum_map_title = serializers.CharField(source="curriculum_map.title", read_only=True)

    class Meta:
        model = Unit
        fields = ["unit_id", "school_id", "curriculum_map_id", "curriculum_version_id", "curriculum_map_title", "sequence", "title", "description", "overview", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _scope_relation_field(self, "curriculum_map_id", CurriculumMap)
        _scope_relation_field(self, "curriculum_version_id", CurriculumMapVersion)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        school_id = _request_school_id(self)
        curriculum_map = attrs.get("curriculum_map") or getattr(self.instance, "curriculum_map", None)
        version = attrs.get("curriculum_version") or getattr(self.instance, "curriculum_version", None)
        if curriculum_map is None or version is None:
            raise serializers.ValidationError("Curriculum map and version are required.")
        if school_id and (str(curriculum_map.school_id) != school_id or str(version.school_id) != school_id):
            raise serializers.ValidationError("Curriculum map and version must belong to the current school.")
        if version.curriculum_map_id != curriculum_map.id:
            raise serializers.ValidationError("Curriculum version must belong to the selected curriculum map.")
        if version.status != CurriculumMapVersion.Status.DRAFT:
            raise serializers.ValidationError("Only draft curriculum versions may be authored.")
        if self.instance is not None and (curriculum_map.id != self.instance.curriculum_map_id or version.id != self.instance.curriculum_version_id):
            raise serializers.ValidationError("A unit cannot be moved to another map or version; clone the version instead.")
        return attrs


class LessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    unit_id = serializers.PrimaryKeyRelatedField(source="unit", queryset=Unit.objects.none())
    unit_title = serializers.CharField(source="unit.title", read_only=True)
    curriculum_version_id = serializers.UUIDField(source="unit.curriculum_version.id", read_only=True)

    class Meta:
        model = Lesson
        fields = ["lesson_id", "school_id", "unit_id", "unit_title", "curriculum_version_id", "sequence", "title", "description", "objectives", "resources", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _scope_relation_field(self, "unit_id", Unit)

    def validate_unit_id(self, unit):
        school_id = _request_school_id(self)
        if school_id and str(unit.school_id) != school_id:
            raise serializers.ValidationError("Unit must belong to the current school.")
        if unit.curriculum_version.status != CurriculumMapVersion.Status.DRAFT:
            raise serializers.ValidationError("Only lessons in draft curriculum versions may be authored.")
        if self.instance is not None and unit.id != self.instance.unit_id:
            raise serializers.ValidationError("A lesson cannot be moved to another unit; clone the version instead.")
        return unit
