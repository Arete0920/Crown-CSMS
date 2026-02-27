import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone

# ---------------------------------------------------------------------------
# Canonical statuses
# ---------------------------------------------------------------------------
STATUS_DRAFT = "DRAFT"
STATUS_SUBMITTED = "SUBMITTED"
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_NEEDS_INFO = "NEEDS_INFO"

SERVICE_LOG_STATUSES = [
    (STATUS_DRAFT, "Draft"),
    (STATUS_SUBMITTED, "Submitted"),
    (STATUS_NEEDS_INFO, "Needs Info"),
    (STATUS_APPROVED, "Approved"),
    (STATUS_REJECTED, "Rejected"),
]

PARTICIPANT_STUDENT = "STUDENT"
PARTICIPANT_PARENT = "PARENT"
PARTICIPANT_STAFF = "STAFF"

PARTICIPANT_TYPES = [
    (PARTICIPANT_STUDENT, "Student"),
    (PARTICIPANT_PARENT, "Parent"),
    (PARTICIPANT_STAFF, "Staff"),
]


# ---------------------------------------------------------------------------
# Abstract base — Crown canon: every row owned by a school_id UUID
# ---------------------------------------------------------------------------
class TenantOwnedModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# PartnerOrganization
# ---------------------------------------------------------------------------
class PartnerOrganization(TenantOwnedModel):
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")

    address_line1 = models.CharField(max_length=255, blank=True, default="")
    address_line2 = models.CharField(max_length=255, blank=True, default="")
    city = models.CharField(max_length=120, blank=True, default="")
    state = models.CharField(max_length=50, blank=True, default="")
    postal_code = models.CharField(max_length=25, blank=True, default="")

    category = models.CharField(max_length=120, blank=True, default="")
    approved = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default="")

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Opportunity
# ---------------------------------------------------------------------------
class Opportunity(TenantOwnedModel):
    partner = models.ForeignKey(
        PartnerOrganization, on_delete=models.PROTECT, related_name="opportunities"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    location = models.CharField(max_length=255, blank=True, default="")

    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    capacity = models.PositiveIntegerField(null=True, blank=True)

    min_grade = models.PositiveSmallIntegerField(null=True, blank=True)
    max_grade = models.PositiveSmallIntegerField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.partner.name})"


# ---------------------------------------------------------------------------
# ServiceGoal
# ---------------------------------------------------------------------------
class ServiceGoal(TenantOwnedModel):
    name = models.CharField(max_length=255, default="Service Hours Requirement")
    school_year = models.CharField(max_length=9, blank=True, default="")
    grade = models.PositiveSmallIntegerField(null=True, blank=True)
    program_tag = models.CharField(max_length=80, blank=True, default="")

    required_hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    due_date = models.DateField(null=True, blank=True)
    active = models.BooleanField(default=True)


# ---------------------------------------------------------------------------
# ReflectionPrompt
# ---------------------------------------------------------------------------
class ReflectionPrompt(TenantOwnedModel):
    title = models.CharField(max_length=255)
    prompt = models.TextField()
    active = models.BooleanField(default=True)


# ---------------------------------------------------------------------------
# ServiceLog
# ---------------------------------------------------------------------------
class ServiceLog(TenantOwnedModel):
    participant_type = models.CharField(
        max_length=10, choices=PARTICIPANT_TYPES, default=PARTICIPANT_STUDENT
    )
    student = models.ForeignKey(
        "core.Student", on_delete=models.PROTECT, null=True, blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="service_logs_user",
    )

    opportunity = models.ForeignKey(
        Opportunity, on_delete=models.SET_NULL, null=True, blank=True
    )
    partner = models.ForeignKey(
        PartnerOrganization, on_delete=models.PROTECT, null=True, blank=True
    )

    service_date = models.DateField(default=timezone.now)
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    description = models.CharField(max_length=255, blank=True, default="")

    reflection_prompt = models.ForeignKey(
        ReflectionPrompt, on_delete=models.SET_NULL, null=True, blank=True
    )
    reflection_text = models.TextField(blank=True, default="")

    status = models.CharField(
        max_length=15, choices=SERVICE_LOG_STATUSES, default=STATUS_DRAFT
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="service_logs_reviewed",
    )
    reviewer_notes = models.TextField(blank=True, default="")

    external_verifier_name = models.CharField(max_length=255, blank=True, default="")
    external_verifier_email = models.EmailField(blank=True, default="")

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "status"]),
            models.Index(fields=["school_id", "service_date"]),
            models.Index(fields=["school_id", "participant_type"]),
        ]


# ---------------------------------------------------------------------------
# VerificationToken
# ---------------------------------------------------------------------------
class VerificationToken(TenantOwnedModel):
    service_log = models.OneToOneField(
        ServiceLog, on_delete=models.CASCADE, related_name="verification_token"
    )
    token = models.CharField(max_length=64, unique=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by_email = models.EmailField(blank=True, default="")


# ---------------------------------------------------------------------------
# Badge + BadgeAward
# ---------------------------------------------------------------------------
class Badge(TenantOwnedModel):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    threshold_hours = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    active = models.BooleanField(default=True)


class BadgeAward(TenantOwnedModel):
    badge = models.ForeignKey(Badge, on_delete=models.PROTECT)
    student = models.ForeignKey("core.Student", on_delete=models.PROTECT)
    awarded_at = models.DateTimeField(auto_now_add=True)
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        unique_together = ("school_id", "badge", "student")
