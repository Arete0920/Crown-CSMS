from __future__ import annotations

from rest_framework import serializers

from .models import CurriculumCourse, CurriculumUnit, CurriculumLesson


class CurriculumLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurriculumLesson
        fields = [
            "id",
            "order",
            "title",
            "planned_date",
            "objective",
            "activities",
            "assessment",
            "worldview_focus",
            "scripture_ref",
            "scripture_text",
            "resources",
        ]


class CurriculumUnitSerializer(serializers.ModelSerializer):
    lessons = CurriculumLessonSerializer(many=True, read_only=True)

    class Meta:
        model = CurriculumUnit
        fields = [
            "id",
            "order",
            "title",
            "start_date",
            "end_date",
            "essential_question",
            "big_idea",
            "worldview_focus",
            "scripture_ref",
            "scripture_text",
            "lessons",
        ]


class CurriculumCourseSerializer(serializers.ModelSerializer):
    units = CurriculumUnitSerializer(many=True, read_only=True)

    class Meta:
        model = CurriculumCourse
        fields = [
            "id",
            "code",
            "name",
            "subject",
            "grade_level",
            "description",
            "worldview_theme",
            "anchor_scripture_ref",
            "anchor_scripture_text",
            "is_active",
            "units",
        ]
