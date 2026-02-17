from __future__ import annotations
import uuid
from django.conf import settings
from django.db import models

class ServiceEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    school = models.ForeignKey("core.School", on_delete=models.CASCADE, related_name="service_entries")
    student = models.ForeignKey("core.Student", on_delete=models.CASCADE, related_name="service_entries")

    date = models.DateField()
    hours = models.DecimalField(max_digits=5, decimal_places=2)
    category = models.CharField(max_length=80, blank=True, default="")
    organization = models.CharField(max_length=120, blank=True, default="")
    supervisor_name = models.CharField(max_length=120, blank=True, default="")
    supervisor_contact = models.CharField(max_length=120, blank=True, default="")

    notes = models.TextField(blank=True, default="")

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")

    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["school", "status"]),
            models.Index(fields=["school", "student"]),
            models.Index(fields=["school", "date"]),
        ]
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"ServiceEntry({self.student_id}, {self.hours}h, {self.status})"
