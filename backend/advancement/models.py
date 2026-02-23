from django.db import models
import uuid


class Donor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, default="")
    source = models.CharField(max_length=120, blank=True, default="")
    lifetime_giving = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-lifetime_giving"]

    def __str__(self):
        return self.name


class Campaign(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("upcoming", "Upcoming"),
        ("closing", "Closing"),
        ("completed", "Completed"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    name = models.CharField(max_length=200)
    goal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    raised = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    donors_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="upcoming")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
