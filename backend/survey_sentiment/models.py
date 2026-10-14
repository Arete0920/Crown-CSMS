# Recovered from CROWN's own historical, unmerged survey implementation.
# Database foundation only; public endpoints are intentionally not enabled.
from __future__ import annotations

import uuid
from django.db import models


class SurveyDefinition(models.Model):
    PURPOSE_CHOICES = [
        ("inquiry", "Inquiry"), ("post_tour", "Post Tour"), ("new_family", "New Family"),
        ("parent_pulse", "Parent Pulse"), ("reenrollment_intent", "Re-enrollment Intent"),
        ("lost_prospect", "Lost Prospect"), ("exit", "Exit"), ("custom", "Custom"),
    ]
    STATUS_CHOICES = [("draft", "Draft"), ("active", "Active"), ("closed", "Closed"), ("archived", "Archived")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="surveys")
    name = models.CharField(max_length=180)
    purpose = models.CharField(max_length=32, choices=PURPOSE_CHOICES, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    anonymous_allowed = models.BooleanField(default=False)
    public_enabled = models.BooleanField(default=False)
    public_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    public_expires_at = models.DateTimeField(null=True, blank=True)
    linked_campaign_id = models.UUIDField(null=True, blank=True)
    grade_code = models.CharField(max_length=3, blank=True, default="")
    audience = models.CharField(max_length=80, blank=True, default="families")
    created_by_user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school", "purpose", "status"])]
        ordering = ["-updated_at"]


class SurveyQuestion(models.Model):
    TYPE_CHOICES = [("scale", "Scale"), ("choice", "Choice"), ("multi", "Multiple Choice"), ("text", "Text"), ("boolean", "Boolean")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(SurveyDefinition, on_delete=models.CASCADE, related_name="questions")
    prompt = models.CharField(max_length=300)
    question_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    key = models.CharField(max_length=64)
    choices = models.JSONField(default=list, blank=True)
    required = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    strategic_tags = models.JSONField(default=list, blank=True)

    class Meta:
        unique_together = ("survey", "key")
        ordering = ["sort_order", "id"]


class SurveyResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="survey_responses")
    survey = models.ForeignKey(SurveyDefinition, on_delete=models.CASCADE, related_name="responses")
    publication = models.ForeignKey("SurveyPublication", null=True, blank=True, on_delete=models.PROTECT, related_name="responses")
    household_id = models.UUIDField(null=True, blank=True)
    application_id = models.UUIDField(null=True, blank=True)
    student_id = models.UUIDField(null=True, blank=True)
    campaign_id = models.UUIDField(null=True, blank=True)
    anonymous = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    metadata_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=["school", "survey", "submitted_at"])]
        ordering = ["-submitted_at"]


class SurveyAnswer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(SurveyQuestion, on_delete=models.PROTECT, related_name="answers")
    value_json = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("response", "question")


class SurveyPublication(models.Model):
    """An independent snapshot of one approved instrument version.

    Public collection and exports remain disabled until their own gates pass.
    The service freezes published rows; direct ORM writes must be prohibited by
    operational policy and reviewed separately before production certification.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    survey = models.ForeignKey(SurveyDefinition, on_delete=models.PROTECT, related_name="publications")
    version = models.PositiveIntegerField()
    snapshot_json = models.JSONField(default=dict)
    snapshot_sha256 = models.CharField(max_length=64)
    respondent_notice = models.TextField()
    collection_mode = models.CharField(max_length=20, default="anonymous")
    published_by_user_id = models.UUIDField()
    published_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["survey", "version"], name="survey_pub_unique_version")]
        ordering = ["version"]


class SurveyRespondentGrant(models.Model):
    """One-use anonymous authority; no respondent identity or raw bearer secret."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    publication = models.ForeignKey(SurveyPublication, on_delete=models.PROTECT)
    token_digest = models.CharField(max_length=64, unique=True)
    publication_sha256 = models.CharField(max_length=64)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    issued_by_user_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    attempts = models.PositiveIntegerField(default=0)


class SurveyCollectionReceipt(models.Model):
    """Neutral retry receipt; never expose this row or response id to clients."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grant = models.OneToOneField(SurveyRespondentGrant, on_delete=models.PROTECT)
    response = models.OneToOneField(SurveyResponse, on_delete=models.CASCADE)
    retry_digest = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
