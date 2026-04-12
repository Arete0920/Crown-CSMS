from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from core.models import AcademicYear
from households.models import Student
from .models import (
    Course, Section, Term, Enrollment, Assignment, AssignmentCategory,
    CurriculumSource, Unit, Lesson, PublisherObjective,
    Submission, Grade, MasteryRecord, TranscriptEntry,
    LessonPlan, LessonResource,
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
    name = serializers.CharField()
    grade_level = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    enrollment_status = serializers.CharField()


class SectionTeacherSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    email = serializers.EmailField()


class SectionTermInfoSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


class SectionCountsSerializer(serializers.Serializer):
    students = serializers.IntegerField()


class SectionRosterResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    section_name = serializers.CharField(allow_blank=True)
    course_code = serializers.CharField(allow_blank=True)
    term = SectionTermInfoSerializer(allow_null=True)
    teacher = SectionTeacherSerializer(allow_null=True)
    students = SectionRosterStudentSerializer(many=True)
    counts = SectionCountsSerializer()


class SectionAssessmentsItemSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    category = serializers.CharField()
    weight = serializers.CharField()
    published = serializers.BooleanField()


class SectionAssessmentsResponseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    assessments = SectionAssessmentsItemSerializer(many=True)


class TranscriptROStudentSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    grade_level = serializers.CharField(allow_blank=True, allow_null=True)


class TranscriptROCourseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    course_code = serializers.CharField(allow_blank=True)
    course_name = serializers.CharField(allow_blank=True)
    teacher_name = serializers.CharField(allow_blank=True)
    final_percent = serializers.FloatField(allow_null=True)
    final_letter = serializers.CharField()
    credits = serializers.FloatField()


class TranscriptROTermSerializer(serializers.Serializer):
    term_id = serializers.UUIDField(allow_null=True)
    term_code = serializers.CharField()
    courses = TranscriptROCourseSerializer(many=True)
    term_gpa_mvp = serializers.FloatField(allow_null=True)


class TranscriptROResponseSerializer(serializers.Serializer):
    student = TranscriptROStudentSerializer()
    terms = TranscriptROTermSerializer(many=True)
    cumulative_gpa_mvp = serializers.FloatField(allow_null=True)
    notes = serializers.ListField(child=serializers.CharField())


class StudentTranscriptCourseSerializer(serializers.Serializer):
    section_id = serializers.UUIDField()
    course_code = serializers.CharField(allow_blank=True)
    course_name = serializers.CharField(allow_blank=True)
    credits = serializers.CharField()
    teacher = serializers.CharField(allow_blank=True)
    final_grade = serializers.CharField(allow_null=True)
    status = serializers.CharField()


class StudentTranscriptTermSerializer(serializers.Serializer):
    term_id = serializers.UUIDField(allow_null=True)
    term_name = serializers.CharField()
    courses = StudentTranscriptCourseSerializer(many=True)


class StudentTranscriptYearSerializer(serializers.Serializer):
    school_year = serializers.CharField()
    terms = StudentTranscriptTermSerializer(many=True)


class StudentTranscriptContractResponseSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    school_years = StudentTranscriptYearSerializer(many=True)


class AssignmentCategoryWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    weight_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=False)
    sort_order = serializers.IntegerField(required=False)
    is_active = serializers.BooleanField(required=False)


class AssignmentCategoryResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    weight_percent = serializers.CharField()
    sort_order = serializers.IntegerField()
    is_active = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class AssignmentCategoryListResponseSerializer(serializers.Serializer):
    categories = AssignmentCategoryResponseSerializer(many=True)


class AssignmentCategoryWeightUpdateSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    weight_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    is_active = serializers.BooleanField()


class AssignmentWriteSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    category_id = serializers.UUIDField(required=False)
    points_possible = serializers.DecimalField(max_digits=8, decimal_places=2, required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    assigned_date = serializers.DateField(required=False, allow_null=True)
    is_published = serializers.BooleanField(required=False)


class AssignmentResponseSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    category_id = serializers.UUIDField()
    category_name = serializers.CharField()
    points_possible = serializers.CharField()
    due_date = serializers.DateField(allow_null=True)
    assigned_date = serializers.DateField(allow_null=True)
    is_published = serializers.BooleanField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class AssignmentListResponseSerializer(serializers.Serializer):
    assignments = AssignmentResponseSerializer(many=True)


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
        ref_name = "AcademicsUnitSerializer"
        fields = ["unit_id", "school_id", "course_id", "course_code", "source_id", "title", "description", "sequence_order"]


class LessonSerializer(serializers.ModelSerializer):
    lesson_id = serializers.UUIDField(source="id", read_only=True)
    unit_id = serializers.UUIDField(read_only=True)
    unit_title = serializers.CharField(source="unit.title", read_only=True)

    class Meta:
        model = Lesson
        ref_name = "AcademicsLessonSerializer"
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

    @extend_schema_field(serializers.CharField())
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

    @extend_schema_field(serializers.CharField(allow_null=True))
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

    @extend_schema_field(serializers.CharField())
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

    @extend_schema_field(serializers.CharField())
    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"


class LessonResourceSerializer(serializers.ModelSerializer):
    resource_id = serializers.UUIDField(source="id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    lesson_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = LessonResource
        fields = [
            "resource_id", "school_id", "lesson_id",
            "title", "kind", "url", "file_ref",
            "created_at", "updated_at",
        ]


class LessonPlanSerializer(serializers.ModelSerializer):
    plan_id = serializers.UUIDField(source="id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    section_id = serializers.UUIDField(read_only=True)
    created_by_id = serializers.UUIDField(read_only=True, allow_null=True)
    updated_by_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = LessonPlan
        fields = [
            "plan_id", "school_id", "section_id", "plan_date",
            "lesson_ids",
            "objectives", "materials", "activities", "homework",
            "teacher_notes_private",
            "created_by_id", "updated_by_id",
            "created_at", "updated_at",
        ]


class LessonPlanPublicSerializer(serializers.ModelSerializer):
    """Read-only serializer for student/parent; omits teacher_notes_private."""
    plan_id = serializers.UUIDField(source="id", read_only=True)
    school_id = serializers.UUIDField(read_only=True)
    section_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = LessonPlan
        fields = [
            "plan_id", "school_id", "section_id", "plan_date",
            "lesson_ids",
            "objectives", "materials", "activities", "homework",
            "created_at", "updated_at",
        ]


class LessonPlanWriteSerializer(serializers.Serializer):
    plan_date = serializers.DateField(required=False)
    lesson_ids = serializers.ListField(child=serializers.CharField(), required=False)
    objectives = serializers.JSONField(required=False)
    materials = serializers.JSONField(required=False)
    activities = serializers.JSONField(required=False)
    homework = serializers.JSONField(required=False)
    teacher_notes_private = serializers.CharField(required=False, allow_blank=True)


class LessonResourceWriteSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    kind = serializers.CharField(required=False)
    url = serializers.CharField(required=False, allow_blank=True)
    file_ref = serializers.CharField(required=False, allow_blank=True)

