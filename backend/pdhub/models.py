from django.db import models
import uuid


class PDResource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=200)
    credit_hours = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title


class PDSession(models.Model):
    STATUS_CHOICES = [
        ("upcoming", "Upcoming"),
        ("in progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=200)
    presenter = models.CharField(max_length=200, blank=True, default="")
    department = models.CharField(max_length=120, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    session_date = models.DateField(null=True, blank=True)
    attendees = models.PositiveIntegerField(default=0)
    satisfaction_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-session_date"]

    def __str__(self):
        return self.title
