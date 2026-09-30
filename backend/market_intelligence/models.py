from __future__ import annotations

import uuid
from django.db import models


class MarketStudy(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("ready", "Ready"), ("active", "Active"), ("archived", "Archived")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="market_studies")
    name = models.CharField(max_length=180)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    analysis_year = models.PositiveIntegerField()
    geography = models.JSONField(default=dict, blank=True)
    population = models.JSONField(default=dict, blank=True)
    economics = models.JSONField(default=dict, blank=True)
    education_market = models.JSONField(default=dict, blank=True)
    faith_community = models.JSONField(default=dict, blank=True)
    competition = models.JSONField(default=dict, blank=True)
    internal_context = models.JSONField(default=dict, blank=True)
    strategic_objectives = models.JSONField(default=dict, blank=True)
    source_provenance = models.JSONField(default=list, blank=True)
    created_by_user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"]), models.Index(fields=["school", "analysis_year"])]
        ordering = ["-analysis_year", "-updated_at"]


class MarketStudyWizardSession(models.Model):
    STATUS_CHOICES = [("draft", "Draft"), ("configured", "Configured"), ("review", "Review"), ("committed", "Committed")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="market_study_wizard_sessions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft", db_index=True)
    current_step = models.PositiveSmallIntegerField(default=1)
    draft_data = models.JSONField(default=dict, blank=True)
    committed_study = models.ForeignKey(MarketStudy, null=True, blank=True, on_delete=models.SET_NULL, related_name="wizard_sessions")
    created_by_user_id = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
        ordering = ["-updated_at"]


class StrategicRecommendation(models.Model):
    CATEGORY_CHOICES = [
        ("tuition", "Tuition"), ("affordability", "Affordability"), ("financial_aid", "Financial Aid"),
        ("enrollment", "Enrollment"), ("program", "Program"), ("marketing", "Marketing"),
        ("transportation", "Transportation"), ("expansion", "Expansion"),
    ]
    PRIORITY_CHOICES = [("low", "Low"), ("medium", "Medium"), ("high", "High")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="strategic_market_recommendations")
    study = models.ForeignKey(MarketStudy, on_delete=models.CASCADE, related_name="recommendations")
    category = models.CharField(max_length=24, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=12, choices=PRIORITY_CHOICES, default="medium")
    title = models.CharField(max_length=180)
    rationale = models.TextField()
    evidence = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default="proposed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "category", "priority"])]
        ordering = ["-created_at"]
