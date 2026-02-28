from __future__ import annotations
import uuid
from django.db import models
from django.db.models import Q
from core.models import School


class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="rooms")
    code = models.CharField(max_length=24)
    name = models.CharField(max_length=120, blank=True, default="")
    capacity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "code"], name="uniq_room_code_per_school"),
            models.CheckConstraint(condition=Q(capacity__gte=0), name="chk_room_capacity_nonneg"),
        ]


class RoomSetupWizardSession(models.Model):
    STATUS = [
        ("draft", "Draft"),
        ("configured", "Configured"),
        ("committed", "Committed"),
        ("verified", "Verified"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS, default="draft")
    rooms = models.JSONField(default=list, blank=True)
    commit_result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["school", "status"])]
