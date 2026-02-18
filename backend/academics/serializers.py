from rest_framework import serializers

from core.models import AcademicYear
from households.models import Student
from .models import (
    Course, Section, Term, Enrollment, Assignment, AssignmentCategory,
    CurriculumSource, Unit, Lesson, PublisherObjective,
    Submission, Grade, MasteryRecord, TranscriptEntry
)


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
            "school_year",
            "start_date",
            "end_date",
            "ordering",
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
            "department",
            "credits",
            "grading_scale_ref",
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
            "teacher_id",
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


# Section Serializers (v1 read-only API)
class SectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for section list view."""
    section_id = serializers.UUIDField(source="id", read_only=True)
    course_id = serializers.UUIDField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    term_id = serializers.UUIDField(source="term_ref_id", read_only=True)
    term_code = serializers.CharField(source="term", read_only=True)
    teacher_id = serializers.UUIDField(read_only=True, allow_null=True)
    teacher_name = serializers.CharField(read_only=True)
    roster_count = serializers.IntegerField(read_only=True, default=0)

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
            "teacher_id",
            "teacher_name",
            "grade_band",
            "roster_count",
        ]


class SectionDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for section detail view."""
    section_id = serializers.UUIDField(source="id", read_only=True)
    course_id = serializers.UUIDField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    term_id = serializers.UUIDField(source="term_ref_id", read_only=True)
    term_code = serializers.CharField(source="term", read_only=True)
    teacher_id = serializers.UUIDField(read_only=True, allow_null=True)
    teacher_name = serializers.CharField(read_only=True)
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
            "teacher_id",
            "teacher_name",
            "grade_band",
            "roster_count",
        ]


class SectionRosterStudentSerializer(serializers.Serializer):
    """Simple student row for roster endpoint."""
    student_id = serializers.UUIDField()
    display_name = serializers.CharField()
    grade_level = serializers.CharField(allow_null=True)
    status = serializers.CharField()


# =============================================================================
# CURRICULUM SERIALIZERS
# =============================================================================


class CurriculumSourceSerializer(serializers.ModelSerializer):
    source_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = CurriculumSource
        fields = ["source_id", "school_id", "name", "source_type", "reference_link", "description"]


class UnitSerializer(serializers.ModelSerializer):
    unit_id = serializers.UUIDField(source="id", read_only=True)
    course_id = serializers.UUIDField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    source_id = serializers.UUIDField(source="curriculum_source_id", read_only=True, allow_null=True)

    class Meta:
        model = Unit
        fields = ["unit_id", "school_id", "course_id", "course_code", "source_id", "title", "description", "sequence_order"]


class LessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="id", read_only=True)
    unit_id = serializers.UUIDField(read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)

    class Meta:
        model = Lesson
        fields = ["lesson_id", "school_id", "unit_id", "unit_title", "title", "lesson_date", "instructional_notes"]


class PublisherObjectiveSerializer(serializers.ModelSerializer):
    objective_id = serializers.UUIDField(source="id", read_only=True)
    lesson_id = serializers.UUIDField(read_only=True)
    lesson_title = serializers.CharField(source="lesson.title", read_only=True)

    class Meta:
        model = PublisherObjective
        fields = ["objective_id", "school_id", "lesson_id", "lesson_title", "objective_code", "description"]


# =============================================================================
# SUBMISSION & GRADE SERIALIZERS
# =============================================================================


class SubmissionSerializer(serializers.ModelSerializer):
    submission_id = serializers.UUIDField(source="id", read_only=True)
    assignment_id = serializers.UUIDField(read_only=True)
    assignment_name = serializers.CharField(source="assignment.name", read_only=True)
    enrollment_id = serializers.UUIDField(read_only=True)
    student_id = serializers.UUIDField(source="enrollment.student_id", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "submission_id", "school_id", "assignment_id", "assignment_name",
            "enrollment_id", "student_id", "student_name",
            "status", "submitted_at", "upload"
        ]
        read_only_fields = ["status", "submitted_at"]

    def get_student_name(self, obj):
        student = obj.enrollment.student
        return f"{student.first_name} {student.last_name}"


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Create submission with file upload."""

    class Meta:
        model = Submission
        fields = ["assignment", "enrollment", "upload"]

    def create(self, validated_data):
        from .services import mark_submission_submitted
        
        submission = super().create(validated_data)
        submission.school_id = submission.assignment.school_id
        submission.save()
        
        mark_submission_submitted(submission)
        return submission


class GradeSerializer(serializers.ModelSerializer):
    grade_id = serializers.UUIDField(source="id", read_only=True)
    submission_id = serializers.UUIDField(read_only=True)
    graded_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = [
            "grade_id", "school_id", "submission_id",
            "graded_by", "graded_by_name",
            "numeric_score", "percentage", "letter_grade",
            "teacher_feedback", "graded_at"
        ]

    def get_graded_by_name(self, obj):
        if obj.graded_by:
            return f"{obj.graded_by.first_name} {obj.graded_by.last_name}"
        return None


class GradeCreateSerializer(serializers.Serializer):
    """Create or update grade for submission."""
    submission_id = serializers.UUIDField()
    numeric_score = serializers.DecimalField(max_digits=7, decimal_places=2)
    teacher_feedback = serializers.CharField(required=False, allow_blank=True, default="")


# =============================================================================
# MASTERY & TRANSCRIPT SERIALIZERS
# =============================================================================


class MasteryRecordSerializer(serializers.ModelSerializer):
    mastery_id = serializers.UUIDField(source="id", read_only=True)
    student_id = serializers.UUIDField(read_only=True)
    student_name = serializers.SerializerMethodField()
    objective_id = serializers.UUIDField(read_only=True)
    objective_code = serializers.CharField(source="objective.objective_code", read_only=True)
    evidence_assignment_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = MasteryRecord
        fields = [
            "mastery_id", "school_id",
            "student_id", "student_name",
            "objective_id", "objective_code",
            "mastery_level", "last_demonstrated_at",
            "evidence_assignment_id"
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class TranscriptEntrySerializer(serializers.ModelSerializer):
    entry_id = serializers.UUIDField(source="id", read_only=True)
    student_id = serializers.UUIDField(read_only=True)
    student_name = serializers.SerializerMethodField()
    course_id = serializers.UUIDField(read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    course_name = serializers.CharField(source="course.name", read_only=True)
    term_id = serializers.UUIDField(read_only=True, allow_null=True)
    term_code = serializers.CharField(source="term.code", read_only=True)

    class Meta:
        model = TranscriptEntry
        fields = [
            "entry_id", "school_id",
            "student_id", "student_name",
            "course_id", "course_code", "course_name",
            "term_id", "term_code",
            "credit_value", "final_letter_grade", "final_percentage", "gpa_points",
            "provider", "dual_enrollment_label"
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

