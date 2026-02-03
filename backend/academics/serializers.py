from rest_framework import serializers

from core.models import AcademicYear
from households.models import Student
from .models import Course, Section, Term


class AcademicYearSerializer(serializers.ModelSerializer):
    school_id = serializers.UUIDField(read_only=True)
    year_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = AcademicYear
        fields = [
            "year_id",
            "school_id",
            "name",
            "start_date",
            "end_date",
            "is_current",
        ]


class TermSerializer(serializers.ModelSerializer):
    term_id = serializers.UUIDField(source="id", read_only=True)
    academic_year_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Term
        fields = [
            "term_id",
            "school_id",
            "academic_year_id",
            "code",
            "name",
            "start_date",
            "end_date",
            "active",
        ]


class CourseSerializer(serializers.ModelSerializer):
    course_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Course
        fields = [
            "course_id",
            "school_id",
            "code",
            "name",
        ]


class SectionSerializer(serializers.ModelSerializer):
    section_id = serializers.UUIDField(source="id", read_only=True)
    course_id = serializers.UUIDField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    term_id = serializers.UUIDField(source="term_ref_id", read_only=True)
    term_code = serializers.CharField(source="term", read_only=True)
    roster_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Section
        fields = [
            "section_id",
            "school_id",
            "course_id",
            "course_code",
            "course_name",
            "term_id",
            "term_code",
            "teacher_name",
            "grade_band",
            "roster_count",
        ]


class StudentSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Student
        fields = [
            "student_id",
            "school_id",
            "household_id",
            "first_name",
            "last_name",
            "grade_level",
        ]
