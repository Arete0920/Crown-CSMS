import uuid
from django.db import models
from django.utils import timezone


class SeedRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # metadata
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    env_name = models.CharField(max_length=32, default="unknown", db_index=True)
    build_sha = models.CharField(max_length=64, default="unknown", db_index=True)

    # scope
    school_id = models.UUIDField(null=True, blank=True, db_index=True)
    command = models.CharField(max_length=128, default="golden_path_bootstrap", db_index=True)
    force = models.BooleanField(default=False)

    # outcome
    status = models.CharField(max_length=16, default="started", db_index=True)  # started|ok|error
    summary_json = models.JSONField(default=dict, blank=True)
    error_text = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
