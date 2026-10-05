import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models

from households.models import Household, Student


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not kwargs.get("raw", False):
            self.clean()
        return super().save(*args, **kwargs)


def _require_same_school(instance, relation_name: str) -> None:
    relation_id = getattr(instance, f"{relation_name}_id", None)
    if relation_id is None:
        return
    try:
        related = getattr(instance, relation_name)
    except ObjectDoesNotExist as exc:
        raise ValidationError(
            {relation_name: "Related record does not exist."}
        ) from exc
    if instance.school_id != related.school_id:
        raise ValidationError(
            {relation_name: "Related record must belong to the same school."}
        )


class ApplicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    SUBMITTED = "SUBMITTED", "Submitted"
    IN_REVIEW = "IN_REVIEW", "In Review"
    DECIDED = "DECIDED", "Decided"


class Application(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    household = models.ForeignKey(
        Household,
        on_delete=models.PROTECT,
        related_name="applications",
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.DRAFT,
        db_index=True,
    )
    checklist_access_key = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    decided_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "application"
        indexes = [
            models.Index(fields=["school_id", "status"]),
            models.Index(fields=["school_id", "created_at"]),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "household")

    def __str__(self) -> str:
        return f"Application {self.id} ({self.status})"


class Applicant(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="applicants",
    )
    student = models.ForeignKey(
        Student,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="applicant_links",
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    grade_applying_for = models.CharField(max_length=16, blank=True, default="")
    dob = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=32, default="other", db_index=True)
    flags = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "applicant"
        indexes = [
            models.Index(fields=["school_id", "application"]),
            models.Index(fields=["school_id", "last_name", "first_name"]),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "application")
        _require_same_school(self, "student")

    def __str__(self) -> str:
        return f"{self.last_name}, {self.first_name}"


class ApplicationEvent(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=60)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "application_event"
        indexes = [
            models.Index(fields=["school_id", "application", "created_at"]),
            models.Index(fields=["school_id", "event_type"]),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "application")

    def __str__(self) -> str:
        return self.event_type


class ChecklistItemStatus(models.TextChoices):
    MISSING = "missing", "Missing"
    SUBMITTED = "submitted", "Submitted"
    UNDER_REVIEW = "under_review", "Under Review"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


class EnrollmentContractStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ISSUED = "issued", "Issued"
    SIGNED = "signed", "Signed"
    COUNTERSIGNED = "countersigned", "Countersigned"
    SUPERSEDED = "superseded", "Superseded"


class ApplicationChecklistItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    item_key = models.CharField(max_length=64)
    title = models.CharField(max_length=120)
    office = models.CharField(max_length=120, blank=True, default="")
    is_required = models.BooleanField(default=True)
    status = models.CharField(
        max_length=32,
        choices=ChecklistItemStatus.choices,
        default=ChecklistItemStatus.MISSING,
        db_index=True,
    )
    notes = models.TextField(blank=True, default="")
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "application_checklist_item"
        constraints = [
            models.UniqueConstraint(
                fields=["application", "item_key"],
                name="uniq_app_checklist_item_key",
            ),
        ]
        indexes = [models.Index(fields=["school_id", "application", "status"])]

    def clean(self):
        super().clean()
        _require_same_school(self, "application")

    def __str__(self) -> str:
        return f"{self.item_key} ({self.status})"


class ApplicationChecklistDocument(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    checklist_item = models.ForeignKey(
        ApplicationChecklistItem,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    file = models.FileField(upload_to="admissions/checklist/%Y/%m/%d")
    original_filename = models.CharField(max_length=255, blank=True, default="")
    content_type = models.CharField(max_length=120, blank=True, default="")
    uploaded_by = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "application_checklist_document"
        indexes = [
            models.Index(fields=["school_id", "checklist_item", "created_at"]),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "checklist_item")

    def __str__(self) -> str:
        return self.original_filename or str(self.id)


class EnrollmentContract(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="enrollment_contracts",
    )
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=32,
        choices=EnrollmentContractStatus.choices,
        default=EnrollmentContractStatus.DRAFT,
        db_index=True,
    )
    line_items = models.JSONField(default=list, blank=True)
    contract_totals = models.JSONField(default=dict, blank=True)
    net_amount_cents = models.BigIntegerField(default=0)
    currency = models.CharField(max_length=3, default="USD")
    payment_plan = models.CharField(max_length=80, blank=True, default="")
    payment_schedule = models.CharField(max_length=255, blank=True, default="")
    responsible_payer = models.CharField(max_length=255, blank=True, default="")
    refund_terms = models.TextField(blank=True, default="")
    note = models.TextField(blank=True, default="")
    issued_at = models.DateTimeField(null=True, blank=True)
    signed_at = models.DateTimeField(null=True, blank=True)
    countersigned_at = models.DateTimeField(null=True, blank=True)
    amended_from = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="amendments",
    )
    created_by = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        db_table = "enrollment_contract"
        constraints = [
            models.UniqueConstraint(
                fields=["application", "version"],
                name="uniq_enrollment_contract_version",
            ),
        ]
        indexes = [models.Index(fields=["school_id", "application", "status"])]

    def clean(self):
        super().clean()
        _require_same_school(self, "application")
        _require_same_school(self, "amended_from")
        if self.amended_from_id and self.application_id != self.amended_from.application_id:
            raise ValidationError(
                {"amended_from": "Amended contract must belong to the same application."}
            )

    def __str__(self) -> str:
        return f"Contract v{self.version} ({self.status})"



class ContractAssentEvidence(models.Model):
    """Append-only evidence that an authenticated actor assented to one exact contract version."""

    class Action(models.TextChoices):
        SIGN = "SIGN", "Sign"
        COUNTERSIGN = "COUNTERSIGN", "Countersign"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    contract = models.ForeignKey(
        EnrollmentContract,
        on_delete=models.PROTECT,
        related_name="assent_evidence",
    )
    action = models.CharField(max_length=16, choices=Action.choices)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="enrollment_contract_assents",
    )
    signer_name = models.CharField(max_length=255)
    signer_email = models.EmailField(blank=True, default="")
    contract_sha256 = models.CharField(max_length=64, db_index=True)
    consent_version = models.CharField(max_length=64, default="crown-contract-assent-v1")
    consent_text = models.TextField()
    accepted_at = models.DateTimeField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True, default="")
    request_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contract_assent_evidence"
        ordering = ["accepted_at", "id"]
        indexes = [
            models.Index(fields=["school_id", "contract", "action"]),
            models.Index(fields=["school_id", "actor_user", "accepted_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["contract", "action", "actor_user", "contract_sha256"],
                name="uniq_contract_actor_assent_digest",
            ),
        ]

    def clean(self):
        super().clean()
        _require_same_school(self, "contract")
        actor_school_id = getattr(self.actor_user, "school_id", None) if self.actor_user_id else None
        if actor_school_id and actor_school_id != self.school_id:
            raise ValidationError({"actor_user": "Actor must belong to the same school."})
        if len(self.contract_sha256) != 64:
            raise ValidationError({"contract_sha256": "A SHA-256 contract digest is required."})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Contract assent evidence is append-only and cannot be modified.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Contract assent evidence is retained and cannot be deleted.")
