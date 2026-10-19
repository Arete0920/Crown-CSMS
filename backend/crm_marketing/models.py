from __future__ import annotations

import uuid
from django.db import models


class LeadStage(models.TextChoices):
    INQUIRY = "inquiry", "Inquiry"
    TOUR_SCHEDULED = "tour_scheduled", "Tour Scheduled"
    APPLICATION_STARTED = "application_started", "Application Started"
    APPLICATION_SUBMITTED = "application_submitted", "Application Submitted"
    ACCEPTED = "accepted", "Accepted"
    ENROLLED = "enrolled", "Enrolled"
    LOST = "lost", "Lost"


class MarketingCampaign(models.Model):
    TYPE_CHOICES = [
        ("capacity_growth", "Capacity Growth"),
        ("referral", "Referral"),
        ("church", "Church Outreach"),
        ("feeder", "Preschool / Feeder"),
        ("general", "General Enrollment"),
    ]
    STATUS_CHOICES = [("draft", "Draft"), ("active", "Active"), ("paused", "Paused"), ("complete", "Complete")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="marketing_campaigns")
    academic_year = models.ForeignKey("core.AcademicYear", null=True, blank=True, on_delete=models.PROTECT, related_name="marketing_campaigns")
    name = models.CharField(max_length=180)
    campaign_type = models.CharField(max_length=32, choices=TYPE_CHOICES, default="general")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    target_grade_code = models.CharField(max_length=3, blank=True, default="")
    enrollment_goal = models.PositiveIntegerField(default=0)
    budget_cents = models.PositiveBigIntegerField(default=0)
    actual_spend_cents = models.PositiveBigIntegerField(default=0)
    tuition_per_student_cents = models.PositiveBigIntegerField(default=0)
    minimum_net_tuition_cents = models.PositiveBigIntegerField(default=0)
    expected_retention_years = models.PositiveSmallIntegerField(default=1)
    target_segment = models.JSONField(default=dict, blank=True)
    portrait_domain_ids = models.JSONField(default=list, blank=True)
    aid_strategy = models.JSONField(default=dict, blank=True)
    created_by_user_id = models.UUIDField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"]), models.Index(fields=["school", "target_grade_code"])]
        ordering = ["-updated_at"]


class MarketingLead(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="marketing_leads")
    campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="leads")
    application = models.ForeignKey("applications.Application", null=True, blank=True, on_delete=models.SET_NULL, related_name="marketing_leads")
    # One family inquiry can produce an application for each child. The existing
    # single FK remains the first-child compatibility projection.
    applications = models.ManyToManyField("applications.Application", blank=True, related_name="inquiry_marketing_leads")
    # Keep legacy API inserts valid while this additive schema precedes its image.
    parent_name = models.CharField(max_length=160, blank=True, default="", db_default="")
    email = models.EmailField(blank=True, default="", db_default="")
    phone = models.CharField(max_length=32, blank=True, default="", db_default="")
    grade_interest = models.CharField(max_length=16, blank=True, default="", db_default="")
    entry_year = models.CharField(max_length=32, blank=True, default="", db_default="")
    campus = models.CharField(max_length=120, blank=True, default="", db_default="")
    request_type = models.CharField(max_length=20, blank=True, default="", db_default="")
    contact_preference = models.CharField(max_length=8, blank=True, default="", db_default="")
    response_consent = models.BooleanField(default=False, db_default=False)
    follow_up_consent = models.BooleanField(default=False, db_default=False)
    family_follow_up_enabled = models.BooleanField(default=False, db_default=False)
    consent_at = models.DateTimeField(null=True, blank=True)
    inquiry_received_at = models.DateTimeField(null=True, blank=True, db_index=True)
    application_started_at = models.DateTimeField(null=True, blank=True)
    attribution_json = models.JSONField(default=dict, db_default={}, blank=True)
    # Public retries are keyed by school + random request key, never by email.
    intake_request_key = models.CharField(max_length=64, null=True, blank=True, unique=True, editable=False)
    intake_payload_digest = models.CharField(max_length=64, blank=True, default="", db_default="", editable=False)
    continuation_nonce = models.UUIDField(null=True, blank=True, editable=False)
    continuation_expires_at = models.DateTimeField(null=True, blank=True, editable=False)
    # Restricted response allowlist for the capability holder's submission retry.
    submission_receipt = models.JSONField(default=dict, db_default={}, blank=True, editable=False)
    stage = models.CharField(max_length=32, choices=LeadStage.choices, default=LeadStage.INQUIRY, db_index=True)
    first_source = models.CharField(max_length=80, blank=True, default="")
    primary_source = models.CharField(max_length=80, blank=True, default="")
    conversion_source = models.CharField(max_length=80, blank=True, default="")
    referral_type = models.CharField(max_length=40, blank=True, default="")
    referral_detail = models.CharField(max_length=180, blank=True, default="")
    assigned_to_user_id = models.UUIDField(null=True, blank=True)
    last_touch_at = models.DateTimeField(null=True, blank=True)
    next_follow_up_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school", "stage"]), models.Index(fields=["school", "campaign", "stage"])]
        ordering = ["-updated_at"]


class CampaignTouchpoint(models.Model):
    CHANNEL_CHOICES = [("email", "Email"), ("phone", "Phone"), ("sms", "SMS"), ("event", "Event"), ("tour", "Tour"), ("referral", "Referral"), ("church", "Church"), ("system", "System")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="marketing_touchpoints")
    campaign = models.ForeignKey(MarketingCampaign, null=True, blank=True, on_delete=models.SET_NULL, related_name="touchpoints")
    lead = models.ForeignKey(MarketingLead, on_delete=models.CASCADE, related_name="touchpoints")
    channel = models.CharField(max_length=24, choices=CHANNEL_CHOICES)
    summary = models.CharField(max_length=240)
    outcome = models.CharField(max_length=120, blank=True, default="")
    metadata_json = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField()
    created_by_user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "occurred_at"]), models.Index(fields=["campaign", "occurred_at"])]
        ordering = ["-occurred_at"]


# Prospective relationship records are intentionally separate from Core household,
# guardian and student identities. These models do not grant portal access.
class _CRMProspectScopeGuard(models.Model):
    """Fail closed on cross-school relations in normal ORM writes.

    All application services must also scope reads/writes; bulk operations and
    raw SQL bypass Django model validation and require separate controls.
    """

    school_relations = ()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        for field in self.school_relations:
            if getattr(self, f"{field}_id", None) is None:
                continue
            related = getattr(self, field)
            if related.school_id != self.school_id:
                from django.core.exceptions import ValidationError

                raise ValidationError({field: "Related record must belong to this school."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class ProspectContact(_CRMProspectScopeGuard):
    """An unverified adult contact; not a Core guardian or account."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="crm_prospect_contacts",
    )
    display_name = models.CharField(max_length=160)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        self.display_name = (self.display_name or "").strip()
        self.email = (self.email or "").strip().lower()
        self.phone = (self.phone or "").strip()
        super().clean()
        if not self.display_name:
            from django.core.exceptions import ValidationError

            raise ValidationError({"display_name": "A contact display name is required."})

    class Meta:
        indexes = [models.Index(fields=["school", "email"], name="crm_pc_school_email_idx")]
        ordering = ["-created_at", "id"]


class ProspectGroup(_CRMProspectScopeGuard):
    """School-owned prospect grouping; never a canonical Core family."""

    school_relations = ("lead",)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="crm_prospect_groups",
    )
    label = models.CharField(max_length=160)
    lead = models.ForeignKey(
        MarketingLead, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="prospect_groups",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        self.label = (self.label or "").strip()
        super().clean()
        if not self.label:
            from django.core.exceptions import ValidationError

            raise ValidationError({"label": "A prospect group label is required."})

    class Meta:
        indexes = [models.Index(fields=["school", "created_at"], name="crm_pg_school_created_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "lead"],
                condition=models.Q(lead__isnull=False),
                name="crm_pg_unique_school_lead",
            ),
        ]
        ordering = ["-created_at", "id"]


class ProspectGroupMember(_CRMProspectScopeGuard):
    """CRM participation only; role is not custody or parent-portal authority."""

    school_relations = ("group", "contact")

    class Role(models.TextChoices):
        PROSPECTIVE_PARENT = "prospective_parent", "Prospective parent"
        OTHER_ADULT = "other_adult", "Other adult"
        CONTACT = "contact", "Contact"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="crm_prospect_group_members",
    )
    group = models.ForeignKey(
        ProspectGroup, on_delete=models.PROTECT, related_name="members",
    )
    contact = models.ForeignKey(
        ProspectContact, on_delete=models.PROTECT, related_name="group_memberships",
    )
    role = models.CharField(
        max_length=24, choices=Role.choices, default=Role.CONTACT,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "group"], name="crm_pgm_school_group_idx")]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "contact"], name="crm_pgm_unique_group_contact",
            ),
        ]
        ordering = ["created_at", "id"]


class EnrollmentInterest(_CRMProspectScopeGuard):
    """One prospective learner and entry year, not an admissions decision.

    learner_number disambiguates siblings without requiring minor PII. It stays
    stable across different entry years within the same prospect group.
    """

    school_relations = ("group", "application")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="crm_enrollment_interests",
    )
    group = models.ForeignKey(
        ProspectGroup, on_delete=models.PROTECT, related_name="enrollment_interests",
    )
    learner_number = models.PositiveSmallIntegerField(default=1)
    grade_interest = models.CharField(max_length=16)
    entry_year = models.CharField(max_length=32)
    application = models.ForeignKey(
        "applications.Application", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="crm_enrollment_interests",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        self.grade_interest = (self.grade_interest or "").strip()
        self.entry_year = (self.entry_year or "").strip()
        super().clean()
        errors = {}
        if not self.grade_interest:
            errors["grade_interest"] = "The grade of interest is required."
        if not self.entry_year:
            errors["entry_year"] = "The entry year is required."
        if self.learner_number is not None and self.learner_number < 1:
            errors["learner_number"] = "Learner number must be positive."
        if errors:
            raise ValidationError(errors)

    class Meta:
        indexes = [
            models.Index(fields=["school", "entry_year"], name="crm_ei_school_year_idx"),
            models.Index(fields=["school", "group"], name="crm_ei_school_group_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["group", "learner_number", "entry_year"],
                name="crm_ei_unique_learner_year",
            ),
            models.UniqueConstraint(
                fields=["school", "application"],
                condition=models.Q(application__isnull=False),
                name="crm_ei_unique_application",
            ),
        ]
        ordering = ["entry_year", "learner_number", "id"]


class CRMTask(_CRMProspectScopeGuard):
    """Durable internal relationship work, not a message dispatch or SIS record."""

    school_relations = ("lead", "group")

    class Kind(models.TextChoices):
        CALL = "call", "Phone call"
        TOUR = "tour", "Tour follow-up"
        APPLICATION = "application", "Application assistance"
        OTHER = "other", "Other staff follow-up"

    class State(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        DONE = "done", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="crm_tasks",
    )
    lead = models.ForeignKey(
        MarketingLead, null=True, blank=True, on_delete=models.PROTECT,
        related_name="crm_tasks",
    )
    group = models.ForeignKey(
        ProspectGroup, null=True, blank=True, on_delete=models.PROTECT,
        related_name="crm_tasks",
    )
    title = models.CharField(max_length=160)
    kind = models.CharField(max_length=24, choices=Kind.choices, default=Kind.OTHER)
    state = models.CharField(max_length=20, choices=State.choices, default=State.OPEN)
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.NORMAL)
    assigned_to_user_id = models.UUIDField(null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by_user_id = models.UUIDField(null=True, blank=True)
    created_by_user_id = models.UUIDField()
    # A stable key for retryable actions; no cross-tenant deduplication by email.
    idempotency_key = models.CharField(max_length=128, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils import timezone

        self.title = (self.title or "").strip()
        super().clean()
        errors = {}
        if not self.title:
            errors["title"] = "A staff task title is required."
        if not self.lead_id and not self.group_id:
            errors["lead"] = "An inquiry or prospective relationship is required."
        if self.group_id and self.lead_id and self.group.lead_id not in (None, self.lead_id):
            errors["lead"] = "The task inquiry must match the prospective group."
        if self.due_at is not None and timezone.is_naive(self.due_at):
            errors["due_at"] = "A timezone-aware due date is required."
        done = self.state == self.State.DONE
        if done != (self.completed_at is not None and self.completed_by_user_id is not None):
            errors["state"] = "A completed task must have completion time and actor; other tasks must not."
        if errors:
            raise ValidationError(errors)

    class Meta:
        ordering = ["due_at", "created_at", "id"]
        indexes = [
            models.Index(fields=["school", "state", "due_at"], name="crm_task_state_due_idx"),
            models.Index(fields=["school", "assigned_to_user_id", "state"], name="crm_task_owner_state_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["school", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="crm_task_school_retry_uniq",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        state="done", completed_at__isnull=False,
                        completed_by_user_id__isnull=False,
                    ) |
                    (
                        ~models.Q(state="done") &
                        models.Q(
                            completed_at__isnull=True,
                            completed_by_user_id__isnull=True,
                        )
                    )
                ),
                name="crm_task_completion_consistent",
            ),
        ]


class CRMTaskEvent(_CRMProspectScopeGuard):
    """Append-only staff action audit. Delivery receipts belong to comms."""

    school_relations = ("task",)

    class Kind(models.TextChoices):
        CREATED = "created", "Created"
        ASSIGNED = "assigned", "Assigned"
        COMPLETED = "completed", "Completed"
        REOPENED = "reopened", "Reopened"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School", on_delete=models.CASCADE, related_name="crm_task_events",
    )
    task = models.ForeignKey(
        CRMTask, on_delete=models.PROTECT, related_name="events",
    )
    kind = models.CharField(max_length=24, choices=Kind.choices)
    actor_user_id = models.UUIDField()
    from_state = models.CharField(max_length=20, blank=True, default="")
    to_state = models.CharField(max_length=20, blank=True, default="")
    from_assignee_id = models.UUIDField(null=True, blank=True)
    to_assignee_id = models.UUIDField(null=True, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError

        if not self._state.adding:
            raise ValidationError("CRM task events cannot be amended.")
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ["occurred_at", "id"]
        indexes = [
            models.Index(fields=["school", "task", "occurred_at"], name="crm_te_school_task_time_idx"),
        ]
