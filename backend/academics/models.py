import uuid
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

    # optional teacher reference (string for now; real Staff model comes later)
    teacher_name = models.CharField(max_length=120, blank=True, default="")
    teacher_id = models.UUIDField(null=True, blank=True)

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
