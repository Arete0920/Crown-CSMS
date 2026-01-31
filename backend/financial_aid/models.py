from django.db import models
from django.utils import timezone
import uuid

class AidBucket(models.TextChoices):
    NEED = "need", "Need-Based"
    MISSION = "mission", "Mission-Driven"
    MARKETING = "marketing", "Marketing/Enrollment"
    MERIT = "merit", "Merit-Based"
    HARDSHIP = "hardship", "Hardship/Crisis"

class FinancialAidApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    household_id = models.UUIDField(db_index=True)
    academic_year = models.CharField(max_length=9, db_index=True)
    submitted_at = models.DateTimeField(default=timezone.now)
    household_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    household_size = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=20,
        default="submitted",
        db_index=True,
        choices=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("in_review", "In Review"),
            ("decided", "Decided"),
        ],
    )

class AidAward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    bucket = models.CharField(
        max_length=20,
        db_index=True,
        null=True,
        blank=True,
        choices=AidBucket.choices,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rationale = models.TextField(blank=True, default="")
    approved_by_user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    application = models.ForeignKey(
        FinancialAidApplication,
        on_delete=models.CASCADE,
        related_name="awards",
        null=True,
        blank=True,
    )

class AidAuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=50, db_index=True)
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    actor_user_id = models.UUIDField(null=True, blank=True)
    message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(default=timezone.now)
from django.db import models
from django.utils import timezone
import uuid

# NOTE TO AI TOOLS:
# MVP MODE. Do NOT add base classes/mixins or extra models.
# Do NOT partially patch. Replace the full file if changes are required.
# No abstractions. No future features. Keep it deterministic.


class AidBucket(models.TextChoices):
    NEED = "need", "Need-Based"
    MISSION = "mission", "Mission-Driven"
    MARKETING = "marketing", "Marketing/Enrollment"
    MERIT = "merit", "Merit-Based"
    HARDSHIP = "hardship", "Hardship/Crisis"


class FinancialAidApplication(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    household_id = models.UUIDField(db_index=True)

    academic_year = models.CharField(max_length=9, db_index=True)  # e.g. "2026-2027"
    submitted_at = models.DateTimeField(default=timezone.now)

    household_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    household_size = models.PositiveIntegerField(default=1)

    status = models.CharField(
        max_length=20,
        choices=[
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("in_review", "In Review"),
            ("decided", "Decided"),
        ],
        default="submitted",
        db_index=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "academic_year"]),
            models.Index(fields=["school_id", "status"]),
        ]


class AidAward(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    application = models.ForeignKey(
        "FinancialAidApplication",
        on_delete=models.CASCADE,
        related_name="awards",
        null=True,
        blank=True,
    )

    bucket = models.CharField(
        max_length=20,
        choices=AidBucket.choices,
        db_index=True,
        null=True,
        blank=True,
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    rationale = models.TextField(blank=True, default="")
    approved_by_user_id = models.UUIDField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "bucket"]),
        ]


class AidAuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school_id = models.UUIDField(db_index=True)
    event_type = models.CharField(max_length=50, db_index=True)
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.UUIDField(db_index=True)

    actor_user_id = models.UUIDField(null=True, blank=True)
    message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(default=timezone.now)
