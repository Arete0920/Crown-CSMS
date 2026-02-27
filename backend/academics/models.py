import uuid
from django.conf import settings
from django.db import models
from core.models import AcademicYear, Staff
from households.models import Student


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Term(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="academic_terms",
    )

    code = models.CharField(max_length=24, db_index=True)
    name = models.CharField(max_length=80)
    school_year = models.CharField(max_length=16, blank=True, default="")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    ordering = models.IntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "academic_term"
        indexes = [
            models.Index(fields=["school_id", "academic_year"]),
            models.Index(fields=["school_id", "code"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}".strip()


class Course(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)

    code = models.CharField(max_length=32, db_index=True)
    name = models.CharField(max_length=160)
    department = models.CharField(max_length=80, blank=True, default="")
    credits = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grading_scale_ref = models.UUIDField(null=True, blank=True)

    class Meta:
        db_table = "course"
        indexes = [
            models.Index(fields=["school_id", "code"]),
        ]

    def __str__(self) -> str:
        return f"{self.code} - {self.name}"


class Section(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="sections")

    term_ref = models.ForeignKey(
        Term,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="sections",
    )

    # spine: keep term as string (e.g., "2026-FALL")
    term = models.CharField(max_length=24, db_index=True)

    # FK to User for primary teacher (nullable)
    # Django auto-creates .teacher_id attribute for the FK
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="taught_sections",
    )

    # optional teacher reference (legacy field for backwards compatibility)
    teacher_name = models.CharField(max_length=120, blank=True, default="")

    # optional grade band (string for now)
    grade_band = models.CharField(max_length=32, blank=True, default="")

    class Meta:
        db_table = "section"
        indexes = [
            models.Index(fields=["school_id", "term"]),
            models.Index(fields=["school_id", "course"]),
        ]

    def __str__(self) -> str:
        return f"Section({self.course.code} {self.term})"


class Enrollment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(Student, on_delete=models.PROTECT, related_name="enrollments")

    class Meta:
        db_table = "enrollment"
        constraints = [
            models.UniqueConstraint(fields=["section", "student"], name="uniq_section_student"),
        ]
        indexes = [
            models.Index(fields=["school_id", "section"]),
            models.Index(fields=["school_id", "student"]),
        ]

    def __str__(self) -> str:
        return f"Enrollment({self.student_id} -> {self.section_id})"


class TeacherAssignment(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="teacher_assignments")
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, related_name="teaching_assignments")

    class Meta:
        db_table = "teacher_assignment"
        constraints = [
            models.UniqueConstraint(fields=["section", "staff"], name="uniq_section_staff"),
        ]
        indexes = [
            models.Index(fields=["school_id", "section"]),
            models.Index(fields=["school_id", "staff"]),
        ]

    def __str__(self) -> str:
        return f"TeacherAssignment({self.staff_id} -> {self.section_id})"


class AssignmentCategory(TimeStampedModel):
    """
    Per-section weighting buckets (e.g., Homework, Quiz, Test, Project).
    
    Weight validation: Sum of active category weights for a section must be 0 or 100.
    - 0 means weights not configured yet → fallback to unweighted totals
    - 100 means weights configured → use weighted grading
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="assignment_categories")

    name = models.CharField(max_length=80)
    weight_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "assignment_category"
        constraints = [
            models.UniqueConstraint(fields=["section", "name"], name="uniq_category_section_name"),
        ]
        indexes = [
            models.Index(fields=["school_id", "section"]),
        ]

    def __str__(self) -> str:
        return f"AssignmentCategory({self.section_id} {self.name} {self.weight_percent}%)"


class Assignment(TimeStampedModel):
    """
    Individual assignments within a section and category.
    
    Constraints:
    - points_possible must be > 0 (validated at API level)
    - Unique (section, name) for MVP simplicity
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="assignments")
    category = models.ForeignKey(AssignmentCategory, on_delete=models.PROTECT, related_name="assignments")

    name = models.CharField(max_length=120)
    points_possible = models.DecimalField(max_digits=7, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    assigned_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True)

    # Curriculum links (optional, for standards-based grading)
    lesson = models.ForeignKey("Lesson", on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    objective = models.ForeignKey("PublisherObjective", on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")

    class Meta:
        db_table = "assignment"
        constraints = [
            models.UniqueConstraint(fields=["section", "name"], name="uniq_assignment_section_name"),
        ]
        indexes = [
            models.Index(fields=["school_id", "section"]),
            models.Index(fields=["section", "category"]),
        ]

    def __str__(self) -> str:
        return f"Assignment({self.section_id} {self.category.name} {self.name})"


# =============================================================================
# CURRICULUM HIERARCHY (standards-based instruction)
# =============================================================================


class CurriculumSource(TimeStampedModel):
    """
    Publisher or research-based curriculum source (e.g., BJU Press, Abeka, state standards).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=32, default="publisher")  # publisher, pdf, research, state_standards
    reference_link = models.URLField(blank=True, default="")
    description = models.TextField(blank=True, default="")

    class Meta:
        db_table = "curriculum_source"
        indexes = [
            models.Index(fields=["school_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.source_type})"


class Unit(TimeStampedModel):
    """
    Instructional unit within a course (e.g., "Unit 1: Foundations of Biology").
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="units")
    curriculum_source = models.ForeignKey(CurriculumSource, on_delete=models.SET_NULL, null=True, blank=True, related_name="units")

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    sequence_order = models.PositiveSmallIntegerField(default=1)

    class Meta:
        db_table = "unit"
        ordering = ["sequence_order", "id"]
        indexes = [
            models.Index(fields=["school_id", "course"]),
        ]

    def __str__(self) -> str:
        return f"Unit {self.sequence_order}: {self.title}"


class Lesson(TimeStampedModel):
    """
    Daily lesson plan within a unit.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")

    title = models.CharField(max_length=255)
    lesson_date = models.DateField(null=True, blank=True)
    instructional_notes = models.TextField(blank=True, default="")

    class Meta:
        db_table = "lesson"
        indexes = [
            models.Index(fields=["school_id", "unit"]),
        ]

    def __str__(self) -> str:
        return f"{self.unit}: {self.title}"


class PublisherObjective(TimeStampedModel):
    """
    Learning objective from publisher curriculum (BJU, Abeka) or state standards.
    MVP: Publisher objectives only. Later can generalize to LearningStandard with crosswalks.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="objectives")

    objective_code = models.CharField(max_length=64)
    description = models.TextField()

    class Meta:
        db_table = "publisher_objective"
        constraints = [
            models.UniqueConstraint(fields=["lesson", "objective_code"], name="uniq_objective_lesson_code"),
        ]
        indexes = [
            models.Index(fields=["school_id", "lesson"]),
        ]

    def __str__(self) -> str:
        return f"{self.objective_code}: {self.description[:40]}"


# =============================================================================
# SUBMISSION & GRADING WORKFLOW
# =============================================================================


class Submission(TimeStampedModel):
    """
    Student submission for an assignment. One per (assignment, enrollment).
    Status workflow: assigned → submitted → graded (or missing/late).
    """
    class Status(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        SUBMITTED = "submitted", "Submitted"
        LATE = "late", "Late"
        MISSING = "missing", "Missing"
        GRADED = "graded", "Graded"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    enrollment = models.ForeignKey(Enrollment, on_delete=models.CASCADE, related_name="submissions")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ASSIGNED)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # File upload (MVP)
    upload = models.FileField(upload_to="submissions/", null=True, blank=True)

    class Meta:
        db_table = "submission"
        constraints = [
            models.UniqueConstraint(fields=["assignment", "enrollment"], name="uniq_submission_assignment_enrollment"),
        ]
        indexes = [
            models.Index(fields=["school_id", "assignment"]),
            models.Index(fields=["school_id", "enrollment"]),
        ]

    def __str__(self) -> str:
        return f"Submission({self.assignment_id} - {self.enrollment.student_id} - {self.status})"


class Grade(TimeStampedModel):
    """
    Grade for a submission. OneToOne relationship.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")

    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions"
    )
    numeric_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    percentage = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    letter_grade = models.CharField(max_length=2, default="F")
    teacher_feedback = models.TextField(blank=True, default="")
    graded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "grade"
        indexes = [
            models.Index(fields=["school_id", "submission"]),
        ]

    def __str__(self) -> str:
        return f"Grade({self.submission_id} => {self.letter_grade} {self.percentage}%)"


# =============================================================================
# MASTERY & TRANSCRIPT
# =============================================================================


class MasteryRecord(TimeStampedModel):
    """
    Mastery tracking per (student, objective). Latest evidence replaces.
    Mastery levels: 1=Beginning, 2=Developing, 3=Proficient, 4=Advanced.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="mastery_records")
    objective = models.ForeignKey(PublisherObjective, on_delete=models.CASCADE, related_name="mastery_records")

    mastery_level = models.PositiveSmallIntegerField(default=1)  # 1-4
    last_demonstrated_at = models.DateTimeField(auto_now=True)

    evidence_assignment = models.ForeignKey(
        Assignment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mastery_evidence"
    )

    class Meta:
        db_table = "mastery_record"
        constraints = [
            models.UniqueConstraint(fields=["student", "objective"], name="uniq_mastery_student_objective"),
        ]
        indexes = [
            models.Index(fields=["school_id", "student"]),
            models.Index(fields=["school_id", "objective"]),
        ]

    def __str__(self) -> str:
        return f"Mastery({self.student_id} {self.objective.objective_code} => L{self.mastery_level})"


class LessonPlan(TimeStampedModel):
    """
    Daily lesson plan authored by a teacher for a specific section and date.
    Unique per (school_id, section, plan_date).
    Audience: teacher (full); parent/student (objectives/materials/activities/homework only —
    teacher_notes_private is excluded by serializer for non-staff).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="lesson_plans")
    plan_date = models.DateField(db_index=True)

    # Optional curriculum links: list of Lesson IDs from this app
    lesson_ids = models.JSONField(default=list, blank=True)  # list[str] (UUIDs)

    objectives = models.TextField(blank=True, default="")
    materials = models.TextField(blank=True, default="")
    activities = models.TextField(blank=True, default="")
    homework = models.TextField(blank=True, default="")
    teacher_notes_private = models.TextField(blank=True, default="")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lesson_plans_created",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lesson_plans_updated",
    )

    class Meta:
        db_table = "lesson_plan"
        constraints = [
            models.UniqueConstraint(
                fields=["school_id", "section", "plan_date"],
                name="uniq_lesson_plan_school_section_date",
            )
        ]
        indexes = [
            models.Index(fields=["school_id", "section", "plan_date"]),
        ]

    def __str__(self) -> str:
        return f"LessonPlan({self.section_id} {self.plan_date})"


class LessonResource(TimeStampedModel):
    """
    External resource (link, file, video, doc) attached to a Lesson.
    Keeps resource metadata only; we never store copyrighted content.
    """
    KIND_LINK = "link"
    KIND_FILE = "file"
    KIND_VIDEO = "video"
    KIND_DOC = "doc"
    KIND_CHOICES = [
        (KIND_LINK, "Link"),
        (KIND_FILE, "File"),
        (KIND_VIDEO, "Video"),
        (KIND_DOC, "Document"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="resources")

    title = models.CharField(max_length=255)
    kind = models.CharField(max_length=32, choices=KIND_CHOICES, default=KIND_LINK)
    url = models.URLField(blank=True, default="")
    # Reference to internal file service (if Crown has one)
    file_ref = models.CharField(max_length=128, blank=True, default="")

    class Meta:
        db_table = "lesson_resource"
        indexes = [
            models.Index(fields=["school_id", "lesson"]),
        ]

    def __str__(self) -> str:
        return f"LessonResource({self.lesson_id} {self.kind}: {self.title})"


class TranscriptEntry(TimeStampedModel):
    """
    Course-level transcript entry for a student.
    MVP: One entry per (student, course, term).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="transcript_entries")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="transcript_entries")
    term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name="transcript_entries")

    credit_value = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_letter_grade = models.CharField(max_length=2, default="")
    final_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    gpa_points = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    provider = models.CharField(max_length=255, blank=True, default="")
    dual_enrollment_label = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "transcript_entry"
        constraints = [
            models.UniqueConstraint(fields=["student", "course", "term"], name="uniq_transcript_student_course_term"),
        ]
        indexes = [
            models.Index(fields=["school_id", "student"]),
            models.Index(fields=["school_id", "course"]),
        ]

    def __str__(self) -> str:
        return f"Transcript({self.student_id} - {self.course.code} - {self.final_letter_grade})"
