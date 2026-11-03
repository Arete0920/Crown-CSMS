"""Independent, pilot-only SGO commitments; no school aid or payment ownership."""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class SGOOrganization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=240)
    state_of_domicile = models.CharField(max_length=2)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.legal_name


class SGOMembership(models.Model):
    VIEWER = "VIEWER"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"
    ROLES = [(VIEWER, "Viewer"), (REVIEWER, "Reviewer"), (ADMIN, "Administrator")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sgo_memberships")
    role = models.CharField(max_length=16, choices=ROLES)
    active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "user"], name="unique_sgo_member_user"),
        ]


class SGOProgram(models.Model):
    FEDERAL = "FEDERAL_25F"
    STATE = "STATE"
    PRIVATE = "PRIVATE"
    SOURCES = [(FEDERAL, "Federal 25F"), (STATE, "State"), (PRIVATE, "Private")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="programs")
    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=70)
    calendar_year = models.PositiveIntegerField()
    funding_source = models.CharField(max_length=20, choices=SOURCES)
    eligibility_rule_version = models.CharField(max_length=80)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "calendar_year", "eligibility_rule_version"],
                name="unique_sgo_program_policy",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            existing = type(self).objects.filter(pk=self.pk).values(
                "organization_id", "name", "code", "calendar_year",
                "funding_source", "eligibility_rule_version",
            ).first()
            if existing and any(getattr(self, key) != value for key, value in existing.items()):
                raise ValidationError("Program provenance is immutable; create a new policy version.")
        self.full_clean()
        return super().save(*args, **kwargs)


class SGOApplication(models.Model):
    UNREVIEWED = "UNREVIEWED"
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    DECISIONS = [
        (UNREVIEWED, "Unreviewed"),
        (ELIGIBLE, "Reviewer attested eligible"),
        (INELIGIBLE, "Reviewer attested ineligible"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Organization comes only from program; no contradictory organization FK.
    program = models.ForeignKey(SGOProgram, on_delete=models.PROTECT, related_name="applications")
    student_key = models.UUIDField()
    school_key = models.UUIDField()
    eligibility = models.CharField(max_length=16, choices=DECISIONS, default=UNREVIEWED)
    reviewer_evidence_key = models.UUIDField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.PROTECT, related_name="+",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["program", "student_key"], name="unique_sgo_application_student",
            ),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            existing = type(self).objects.filter(pk=self.pk).values(
                "program_id", "student_key", "school_key",
            ).first()
            if existing and any(getattr(self, key) != value for key, value in existing.items()):
                raise ValidationError(
                    "SGO application program, student and school references are immutable."
                )
        self.full_clean()
        return super().save(*args, **kwargs)



class SGOFamilyGrant(models.Model):
    """Explicit synthetic applicant access; never inferred from school or SGO roles."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(SGOProgram, on_delete=models.PROTECT, related_name="family_grants")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    student_key = models.UUIDField()
    school_key = models.UUIDField()
    consent_version = models.CharField(max_length=80)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["program", "student_key"], name="unique_sgo_family_grant"),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            original = type(self).objects.filter(pk=self.pk).values(
                "program_id", "user_id", "student_key", "school_key", "consent_version",
            ).first()
            if original and any(getattr(self, name) != value for name, value in original.items()):
                raise ValidationError("Applicant grant identity and consent version are immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)


class SGOProcessorAssignment(models.Model):
    """Partner-program-scoped demonstration processing; no award authority."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    program = models.ForeignKey(SGOProgram, on_delete=models.PROTECT, related_name="processors")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["program", "user"], name="unique_sgo_processor_assignment"),
        ]


class SGOFamilyIntake(models.Model):
    """Versioned non-PII intake attributes on the existing SGOApplication."""

    SUBMITTED = "SUBMITTED"
    CORRECTION_REQUESTED = "CORRECTION_REQUESTED"
    RESUBMITTED = "RESUBMITTED"
    STATES = [(SUBMITTED, "Submitted"), (CORRECTION_REQUESTED, "Correction requested"),
              (RESUBMITTED, "Resubmitted")]
    GRADES = [(str(i), str(i)) for i in range(1, 13)] + [("K", "Kindergarten")]
    REASONS = [
        ("GRADE_UNVERIFIED", "Grade not verified"),
        ("PROGRAM_DETAIL_MISMATCH", "Program details need verification"),
        ("OTHER_NON_SENSITIVE", "Other non-sensitive correction"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    application = models.OneToOneField(
        SGOApplication, on_delete=models.PROTECT, related_name="family_intake",
    )
    grant = models.OneToOneField(SGOFamilyGrant, on_delete=models.PROTECT, related_name="intake")
    grade_level = models.CharField(max_length=2, choices=GRADES)
    status = models.CharField(max_length=24, choices=STATES, default=SUBMITTED)
    consent_version = models.CharField(max_length=80)
    consented_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    revision = models.PositiveIntegerField(default=1)
    submission_key = models.UUIDField(unique=True)
    requested_reason = models.CharField(max_length=32, choices=REASONS, blank=True)
    last_processor_key = models.UUIDField(null=True, blank=True, unique=True)
    last_correction_key = models.UUIDField(null=True, blank=True, unique=True)

    def clean(self):
        super().clean()
        if self.application_id and self.grant_id:
            if (self.application.program_id != self.grant.program_id
                    or self.application.student_key != self.grant.student_key
                    or self.application.school_key != self.grant.school_key):
                raise ValidationError("Applicant grant and application must refer to the same program and keys.")
            if self.consent_version != self.grant.consent_version:
                raise ValidationError("Recorded consent version must match the authorized program grant.")

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            original = type(self).objects.filter(pk=self.pk).values(
                "application_id", "grant_id", "consent_version", "submission_key", "consented_at",
            ).first()
            if original and any(getattr(self, name) != value for name, value in original.items()):
                raise ValidationError("Family intake identity and original consent are immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)


class SGOAward(models.Model):
    """A commitment is NEVER a funded, cleared, allocated or paid amount."""
    COMMITTED = "COMMITTED"
    CANCELLED = "CANCELLED"
    STATES = [(COMMITTED, "Noncash commitment"), (CANCELLED, "Cancelled commitment")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Organization derives only from application.program.organization.
    application = models.OneToOneField(
        SGOApplication, on_delete=models.PROTECT, related_name="award",
    )
    amount_cents = models.PositiveBigIntegerField()
    status = models.CharField(max_length=16, choices=STATES, default=COMMITTED)
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+",
    )
    committed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount_cents__gt=0), name="sgo_award_amount_positive"),
        ]

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding:
            existing = type(self).objects.filter(pk=self.pk).values(
                "application_id", "amount_cents", "authorized_by_id",
            ).first()
            if existing and any(getattr(self, key) != value for key, value in existing.items()):
                raise ValidationError("Award amount, approval and application are immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)


class SGOAuditEvent(models.Model):
    PROGRAM_CREATED = "PROGRAM_CREATED"
    APPLICATION_CREATED = "APPLICATION_CREATED"
    ELIGIBILITY_ATTESTED = "ELIGIBILITY_ATTESTED"
    AWARD_COMMITTED = "AWARD_COMMITTED_NONCASH"
    AWARD_CANCELLED = "AWARD_CANCELLED_NONCASH"
    INTAKE_SUBMITTED = "INTAKE_SUBMITTED"
    INTAKE_CORRECTION_REQUESTED = "INTAKE_CORRECTION_REQUESTED"
    INTAKE_RESUBMITTED = "INTAKE_RESUBMITTED"
    ACTIONS = [(x, x) for x in (
        PROGRAM_CREATED, APPLICATION_CREATED, ELIGIBILITY_ATTESTED,
        AWARD_COMMITTED, AWARD_CANCELLED,
        INTAKE_SUBMITTED, INTAKE_CORRECTION_REQUESTED, INTAKE_RESUBMITTED,
    )]
    ACTION_KEYS = {
        PROGRAM_CREATED: {"source", "year"},
        APPLICATION_CREATED: set(),
        ELIGIBILITY_ATTESTED: {"outcome"},
        AWARD_COMMITTED: {"amount_cents"},
        AWARD_CANCELLED: set(),
        INTAKE_SUBMITTED: {"revision"},
        INTAKE_CORRECTION_REQUESTED: {"revision", "reason"},
        INTAKE_RESUBMITTED: {"revision", "reason"},
    }
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="audit_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=70, choices=ACTIONS)
    subject_key = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)
    happened_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "happened_at"], name="sgo_audit_org_time"),
        ]

    def clean(self):
        super().clean()
        value = self.metadata
        if not isinstance(value, dict) or set(value) != self.ACTION_KEYS.get(self.action):
            raise ValidationError({"metadata": "Metadata keys must match fixed action allowlist."})
        if self.action == self.PROGRAM_CREATED:
            if (value["source"] not in dict(SGOProgram.SOURCES)
                    or type(value["year"]) is not int
                    or not 2026 <= value["year"] <= 2100):
                raise ValidationError({"metadata": "Invalid program metadata."})
        elif self.action == self.ELIGIBILITY_ATTESTED:
            if value["outcome"] not in (SGOApplication.ELIGIBLE, SGOApplication.INELIGIBLE):
                raise ValidationError({"metadata": "Invalid outcome."})
        elif self.action in (self.INTAKE_SUBMITTED, self.INTAKE_CORRECTION_REQUESTED,
                             self.INTAKE_RESUBMITTED):
            if type(value["revision"]) is not int or value["revision"] < 1:
                raise ValidationError({"metadata": "Invalid intake revision."})
            if self.action != self.INTAKE_SUBMITTED and value["reason"] not in dict(SGOFamilyIntake.REASONS):
                raise ValidationError({"metadata": "Unsupported correction reason."})
        elif self.action == self.AWARD_COMMITTED:
            if (type(value["amount_cents"]) is not int
                    or not 0 < value["amount_cents"] <= 9_000_000_000_000_000):
                raise ValidationError({"metadata": "Invalid commitment amount."})

    def save(self, *args, **kwargs):
        if self.pk and not self._state.adding and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit events are append-only.")
        self.full_clean()
        return super().save(*args, **kwargs)
