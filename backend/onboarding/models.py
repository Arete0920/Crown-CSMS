"""
onboarding/models.py

ImportSession tracks a single bulk-import lifecycle:
  pending → uploaded → validated → previewed → committed → verified

Tenant-scoped via school FK (enforced in views via get_request_school_id).
Raw CSV is stored as text to avoid media/storage config complexity (MVP).
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import School

User = get_user_model()


class ImportSession(models.Model):
    MODE_STUDENTS_GUARDIANS = 'students_guardians'
    MODE_STAFF = 'staff'
    MODE_CONTACTS = 'contacts'
    MODE_CHOICES = [
        (MODE_STUDENTS_GUARDIANS, 'Students + Guardians'),
        (MODE_STAFF, 'Staff / Teachers'),
        (MODE_CONTACTS, 'Emergency Contacts'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_UPLOADED = 'uploaded'
    STATUS_VALIDATED = 'validated'
    STATUS_PREVIEWED = 'previewed'
    STATUS_COMMITTED = 'committed'
    STATUS_VERIFIED = 'verified'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_UPLOADED, 'Uploaded'),
        (STATUS_VALIDATED, 'Validated'),
        (STATUS_PREVIEWED, 'Previewed'),
        (STATUS_COMMITTED, 'Committed'),
        (STATUS_VERIFIED, 'Verified'),
    ]

    # Tenant scoping — enforced on every view
    school = models.ForeignKey(
        School,
        on_delete=models.PROTECT,
        related_name='import_sessions',
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='import_sessions',
    )

    mode = models.CharField(max_length=50, choices=MODE_CHOICES, default=MODE_STUDENTS_GUARDIANS)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)

    # CSV storage (raw text, clears after commit for PII hygiene)
    filename = models.CharField(max_length=255, blank=True)
    raw_csv = models.TextField(blank=True)

    # Row/entity counts (populated on upload + validated)
    rows_total = models.IntegerField(default=0)
    students_detected = models.IntegerField(default=0)
    guardians_detected = models.IntegerField(default=0)
    households_detected = models.IntegerField(default=0)

    # Validation + commit results (stored as JSON)
    validate_result = models.JSONField(null=True, blank=True)
    commit_result = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"ImportSession({self.id}, school={self.school_id}, mode={self.mode}, status={self.status})"
