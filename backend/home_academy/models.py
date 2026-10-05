from django.db import models
from django.utils import timezone


PROGRAM_TYPES = [
    ("support_only", "Support Only"),
    ("umbrella_school", "Umbrella / School of Record"),
    ("hybrid_academy", "Hybrid Academy"),
    ("supplemental_course_only", "Supplemental Course Only"),
    ("diploma_track", "Diploma Track"),
]

ENROLLMENT_STATUSES = [
    ("standard_enrollment", "Standard Enrollment"),
    ("homeschool_affiliate", "Homeschool Affiliate"),
    ("homeschool_course_only", "Homeschool Course Only"),
    ("homeschool_lab_only", "Homeschool Lab Only"),
    ("homeschool_hybrid", "Homeschool Hybrid"),
    ("homeschool_school_of_record", "Homeschool School of Record"),
    ("homeschool_diploma_track", "Homeschool Diploma Track"),
    ("homeschool_support_only", "Homeschool Support Only"),
]

SCHOOL_OF_RECORD_STATUSES = [
    ("none", "None"),
    ("parent_is_record", "Parent Is School of Record"),
    ("school_is_record", "School Is School of Record"),
    ("outside_school_is_record", "Outside School Is School of Record"),
]

DIPLOMA_ELIGIBILITY_STATUSES = [
    ("not_eligible", "Not Eligible"),
    ("eligible_pending", "Eligible Pending Requirements"),
    ("eligible_approved", "Eligible Approved"),
    ("not_approved", "Not Approved"),
]

OFFERING_TYPES = [
    ("academic_course", "Academic Course"),
    ("lab", "Lab"),
    ("sport", "Sport"),
    ("music", "Music"),
    ("drama", "Drama"),
    ("art", "Art"),
    ("chapel", "Chapel"),
    ("club", "Club"),
    ("student_life", "Student Life"),
    ("event", "Event"),
    ("testing", "Testing"),
    ("transcript_review", "Transcript Review"),
    ("graduation_audit", "Graduation Audit"),
    ("dual_enrollment_support", "Dual Enrollment Support"),
]

BILLING_FREQUENCIES = [
    ("one_time", "One Time"),
    ("monthly", "Monthly"),
    ("semester", "Semester"),
    ("season", "Season"),
    ("annual", "Annual"),
    ("per_event", "Per Event"),
    ("per_lesson", "Per Lesson"),
]

ENROLLMENT_REQUEST_STATUSES = [
    ("requested", "Requested"),
    ("pending_eligibility", "Pending Eligibility"),
    ("eligible", "Eligible"),
    ("waitlisted", "Waitlisted"),
    ("approved", "Approved"),
    ("active", "Active"),
    ("denied", "Denied"),
    ("cancelled", "Cancelled"),
    ("completed", "Completed"),
]

PAYMENT_STATUSES = [
    ("not_required", "Not Required"),
    ("pending", "Pending"),
    ("paid", "Paid"),
    ("past_due", "Past Due"),
    ("waived", "Waived"),
]

FORM_STATUSES = [
    ("not_required", "Not Required"),
    ("missing", "Missing"),
    ("complete", "Complete"),
]

AID_CHARGE_TYPES = [
    ("tuition", "Tuition"),
    ("course_fee", "Course Fee"),
    ("lab_fee", "Lab Fee"),
    ("activity_fee", "Activity Fee"),
    ("athletic_fee", "Athletic Fee"),
    ("materials_fee", "Materials Fee"),
    ("uniform_fee", "Uniform Fee"),
    ("testing_fee", "Testing Fee"),
    ("transcript_fee", "Transcript Fee"),
    ("graduation_audit_fee", "Graduation Audit Fee"),
    ("diploma_fee", "Diploma Fee"),
    ("platform_fee", "Platform Fee"),
]


class HomeAcademyProgram(models.Model):
    """School-branded Home Academy / homeschool affiliation program configuration."""

    school_id = models.UUIDField(db_index=True, unique=True)
    public_program_name = models.CharField(max_length=160)
    program_type = models.CharField(max_length=40, choices=PROGRAM_TYPES, default="support_only")
    handbook_document_id = models.CharField(max_length=120, blank=True)
    active_school_year = models.CharField(max_length=20, blank=True)
    default_sports_min_academic_courses = models.PositiveSmallIntegerField(default=2)
    default_activity_min_academic_courses = models.PositiveSmallIntegerField(default=1)
    default_homeschool_seat_cap = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school_id", "is_active"])]

    def __str__(self):
        return f"HomeAcademyProgram({self.school_id}, {self.public_program_name})"


class HomeAcademyEnrollment(models.Model):
    """Student relationship to the school's Home Academy program."""

    school_id = models.UUIDField(db_index=True)
    student_id = models.UUIDField(db_index=True)
    household_id = models.UUIDField(null=True, blank=True, db_index=True)
    program = models.ForeignKey(
        HomeAcademyProgram,
        on_delete=models.CASCADE,
        related_name="enrollments",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=50, choices=ENROLLMENT_STATUSES, default="homeschool_affiliate")
    school_of_record_status = models.CharField(
        max_length=40,
        choices=SCHOOL_OF_RECORD_STATUSES,
        default="parent_is_record",
    )
    diploma_eligibility_status = models.CharField(
        max_length=40,
        choices=DIPLOMA_ELIGIBILITY_STATUSES,
        default="not_eligible",
    )
    grade_level = models.CharField(max_length=20, blank=True)
    advisor_id = models.UUIDField(null=True, blank=True)
    registrar_id = models.UUIDField(null=True, blank=True)
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "student_id", "is_active"]),
            models.Index(fields=["school_id", "status"]),
        ]
        unique_together = [("school_id", "student_id", "program")]

    @property
    def is_school_of_record(self) -> bool:
        return self.school_of_record_status == "school_is_record"

    @property
    def is_diploma_track(self) -> bool:
        return self.status == "homeschool_diploma_track"

    def __str__(self):
        return f"HomeAcademyEnrollment({self.school_id}, student={self.student_id}, {self.status})"


class Offering(models.Model):
    """A school-approved academic, athletic, arts, chapel, testing, or service offering."""

    school_id = models.UUIDField(db_index=True)
    program = models.ForeignKey(
        HomeAcademyProgram,
        on_delete=models.CASCADE,
        related_name="offerings",
        null=True,
        blank=True,
    )
    offering_type = models.CharField(max_length=40, choices=OFFERING_TYPES, db_index=True)
    title = models.CharField(max_length=180)
    description = models.TextField(blank=True)
    school_year = models.CharField(max_length=20, blank=True)
    term = models.CharField(max_length=40, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, default=0)
    billing_frequency = models.CharField(max_length=20, choices=BILLING_FREQUENCIES, default="one_time")
    academic_course_id = models.UUIDField(null=True, blank=True, db_index=True)
    academic_term_id = models.UUIDField(null=True, blank=True, db_index=True)
    credit_bearing = models.BooleanField(default=False)
    transcript_eligible = models.BooleanField(default=False)
    diploma_track_eligible = models.BooleanField(default=False)
    requires_academic_anchor = models.BooleanField(default=True)
    min_academic_courses_required = models.PositiveSmallIntegerField(default=0)
    requires_school_of_record = models.BooleanField(default=False)
    requires_admin_approval = models.BooleanField(default=True)
    requires_coach_or_director_approval = models.BooleanField(default=False)
    blocks_if_past_due = models.BooleanField(default=True)
    blocks_if_forms_missing = models.BooleanField(default=True)
    total_capacity = models.PositiveIntegerField(default=0)
    reserved_full_time_seats = models.PositiveIntegerField(default=0)
    homeschool_seat_cap = models.PositiveIntegerField(default=0)
    buffer_seats = models.PositiveIntegerField(default=0)
    waitlist_enabled = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    staff_owner_id = models.UUIDField(null=True, blank=True)
    location = models.CharField(max_length=160, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "offering_type", "active"]),
            models.Index(fields=["school_id", "school_year", "term"]),
        ]

    def save(self, *args, **kwargs):
        if self.offering_type == "sport" and self.min_academic_courses_required == 0:
            self.min_academic_courses_required = 2
        elif self.offering_type in {"music", "drama", "art", "club"} and self.min_academic_courses_required == 0:
            self.min_academic_courses_required = 1
        elif self.offering_type in {"academic_course", "lab"}:
            self.credit_bearing = self.credit_bearing or self.offering_type == "academic_course"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Offering({self.school_id}, {self.title})"


class OfferingEnrollment(models.Model):
    """Student registration/roster row for a Home Academy offering."""

    school_id = models.UUIDField(db_index=True)
    student_id = models.UUIDField(db_index=True)
    offering = models.ForeignKey(Offering, on_delete=models.CASCADE, related_name="enrollments")
    home_academy_enrollment = models.ForeignKey(
        HomeAcademyEnrollment,
        on_delete=models.SET_NULL,
        related_name="offering_enrollments",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=40, choices=ENROLLMENT_REQUEST_STATUSES, default="requested")
    eligibility_status = models.CharField(max_length=40, default="pending")
    eligibility_failures = models.JSONField(default=list, blank=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default="pending")
    finance_obligation_id = models.PositiveBigIntegerField(null=True, blank=True, db_index=True)
    form_status = models.CharField(max_length=20, choices=FORM_STATUSES, default="missing")
    roster_status = models.CharField(max_length=40, default="pending")
    transcript_posting_status = models.CharField(max_length=40, default="not_applicable")
    transcript_entry_id = models.UUIDField(null=True, blank=True, db_index=True)
    final_letter_grade = models.CharField(max_length=2, blank=True)
    final_percentage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    aid_eligible = models.BooleanField(default=False)
    financial_aid_rule_id = models.PositiveBigIntegerField(null=True, blank=True)
    admin_approved = models.BooleanField(default=False)
    coach_or_director_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("school_id", "student_id", "offering")]
        indexes = [
            models.Index(fields=["school_id", "student_id"]),
            models.Index(fields=["school_id", "status"]),
        ]

    def __str__(self):
        return f"OfferingEnrollment({self.school_id}, student={self.student_id}, offering={self.offering_id})"


class FinancialAidRule(models.Model):
    """Charge-level aid eligibility rule for Home Academy charges."""

    school_id = models.UUIDField(db_index=True)
    charge_type = models.CharField(max_length=40, choices=AID_CHARGE_TYPES)
    aid_eligible = models.BooleanField(default=False)
    esa_eligible = models.BooleanField(default=False)
    scholarship_eligible = models.BooleanField(default=False)
    requires_academic_anchor = models.BooleanField(default=True)
    max_award_percent = models.PositiveSmallIntegerField(default=0)
    max_award_amount = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("school_id", "charge_type")]
        indexes = [models.Index(fields=["school_id", "charge_type", "active"])]


class TranscriptPostingRule(models.Model):
    """Guardrail for whether an offering can enter transcript staging."""

    offering = models.OneToOneField(Offering, on_delete=models.CASCADE, related_name="transcript_rule")
    requires_registrar_approval = models.BooleanField(default=True)
    transcript_category = models.CharField(max_length=80, blank=True)
    credit_value = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    grade_source = models.CharField(max_length=80, blank=True)
    diploma_requirement_area = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
