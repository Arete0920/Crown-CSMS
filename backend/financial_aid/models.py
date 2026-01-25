import uuid
from decimal import Decimal
from django.db import models
from households.models import Household


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AidStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    DECIDED = "DECIDED", "Decided"


class AwardStatus(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    DENIED = "DENIED", "Denied"


class AidApplication(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    household = models.ForeignKey(Household, on_delete=models.PROTECT, related_name="aid_applications")

    # e.g., "2026-2027"
    academic_year = models.CharField(max_length=16, db_index=True)

    status = models.CharField(max_length=16, choices=AidStatus.choices, default=AidStatus.DRAFT, db_index=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "aid_application"
        indexes = [
            models.Index(fields=["school_id", "academic_year"]),
            models.Index(fields=["school_id", "status"]),
        ]

    def __str__(self) -> str:
        return f"AidApplication({self.academic_year})"


class AidAward(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    aid_application = models.OneToOneField(AidApplication, on_delete=models.CASCADE, related_name="award")
    status = models.CharField(max_length=16, choices=AwardStatus.choices)

    amount_annual = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        db_table = "aid_award"
        indexes = [
            models.Index(fields=["school_id", "status"]),
        ]

    def __str__(self) -> str:
        return f"AidAward({self.status}, {self.amount_annual})"


class AidDisbursement(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    award = models.ForeignKey(AidAward, on_delete=models.CASCADE, related_name="disbursements")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    disbursed_on = models.DateField()

    class Meta:
        db_table = "aid_disbursement"
        indexes = [
            models.Index(fields=["school_id", "disbursed_on"]),
        ]

    def __str__(self) -> str:
        return f"AidDisbursement({self.amount} on {self.disbursed_on})"


class AidEvent(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)

    aid_application = models.ForeignKey(AidApplication, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=60)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "aid_event"
        indexes = [
            models.Index(fields=["school_id", "event_type"]),
            models.Index(fields=["school_id", "aid_application", "created_at"]),
        ]
