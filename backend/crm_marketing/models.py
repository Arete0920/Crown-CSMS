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
