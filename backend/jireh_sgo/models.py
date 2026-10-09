"""Isolated grantor-domain records. No student PII or external cash in this foundation."""
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class SGOOrganization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    legal_name = models.CharField(max_length=240)
    state_of_domicile = models.CharField(max_length=2)
    active = models.BooleanField(default=False)
    # Administrative statement, never evidence of an IRS/state designation.
    federal_listing_verified = models.BooleanField(default=False)
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
    PILOT = "PILOT"
    ENABLED = "ENABLED"
    STATES = [(PILOT, "Pilot - no live settlement"), (ENABLED, "Enabled")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="programs")
    name = models.CharField(max_length=200)
    code = models.SlugField(max_length=70)
    calendar_year = models.PositiveIntegerField()
    funding_source = models.CharField(max_length=20, choices=SOURCES)
    # Version identifies the SGO-approved policy; it does not imply legal certification.
    eligibility_rule_version = models.CharField(max_length=80)
    status = models.CharField(max_length=12, choices=STATES, default=PILOT)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "code", "calendar_year"], name="unique_sgo_program_year"
            ),
        ]


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
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="applications")
    program = models.ForeignKey(SGOProgram, on_delete=models.PROTECT, related_name="applications")
    # Opaque UUID references: no name, DOB, address, SSN, tax records or income here.
    student_key = models.UUIDField()
    school_key = models.UUIDField()
    eligibility = models.CharField(max_length=16, choices=DECISIONS, default=UNREVIEWED)
    reviewer_evidence_key = models.CharField(max_length=80, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "program", "student_key"], name="unique_sgo_application_student"
            ),
        ]


class SGOAward(models.Model):
    """A noncash grantor commitment. It never posts money to a school ledger."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="awards")
    application = models.OneToOneField(SGOApplication, on_delete=models.PROTECT, related_name="award")
    amount_cents = models.PositiveBigIntegerField()
    # No DISBURSED state exists until independently verified remittance is implemented.
    status = models.CharField(max_length=16, default="COMMITTED", choices=[
        ("COMMITTED", "Committed but not funded"),
        ("CANCELLED", "Cancelled"),
    ])
    authorized_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    committed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(amount_cents__gt=0), name="sgo_award_amount_positive"),
        ]


class SGOAuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(SGOOrganization, on_delete=models.PROTECT, related_name="audit_events")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    action = models.CharField(max_length=70)
    subject_key = models.UUIDField()
    metadata = models.JSONField(default=dict, blank=True)
    happened_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["organization", "happened_at"], name="sgo_audit_org_time"),
        ]
