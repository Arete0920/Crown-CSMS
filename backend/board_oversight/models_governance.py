"""
board_oversight/models_governance.py

Stage 4 additions — extend board_oversight with:
  StrategicInitiative  — initiative tracker
  BoardKPISnapshot     — monthly trend snapshots
  RoadmapItem          — public product roadmap
  ReleaseLog           — versioned release notes
"""
from django.db import models


class StrategicInitiative(models.Model):
    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("in_progress", "In Progress"),
        ("complete", "Complete"),
        ("cancelled", "Cancelled"),
    ]

    school_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner_role = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planning")
    target_date = models.DateField(null=True, blank=True)
    progress_percent = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"StrategicInitiative({self.title}, {self.status})"


class BoardKPISnapshot(models.Model):
    """Monthly KPI snapshot powering board trend charts."""
    school_id = models.UUIDField(db_index=True)
    month = models.DateField(db_index=True)  # first day of month (e.g. 2026-02-01)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    enrollment = models.IntegerField(default=0)
    discipline_incidents = models.IntegerField(default=0)
    financial_aid_awards = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("school_id", "month")
        ordering = ["-month"]

    def __str__(self):
        return f"BoardKPISnapshot({self.school_id}, {self.month})"


class RoadmapItem(models.Model):
    STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("released", "Released"),
        ("cancelled", "Cancelled"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="planned")
    target_release = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["target_release", "title"]

    def __str__(self):
        return f"RoadmapItem({self.title}, {self.status})"


class ReleaseLog(models.Model):
    version = models.CharField(max_length=20, unique=True)
    release_date = models.DateField()
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-release_date"]

    def __str__(self):
        return f"ReleaseLog({self.version}, {self.release_date})"
