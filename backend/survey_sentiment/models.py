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
