"""
core/models_export.py

DataDestructionCertificate — immutable record that school data was purged.
"""
import uuid
from django.db import models


class DataDestructionCertificate(models.Model):
    """
    Issued when a school's data is purged. Provides legal evidence of destruction.
    Reference code is generated at creation and never changed.
    """
    school_id = models.UUIDField(db_index=True)
    reference_code = models.CharField(max_length=200, unique=True, default=uuid.uuid4)
    issued_at = models.DateTimeField(auto_now_add=True)
    purged_by = models.CharField(max_length=200, blank=True)  # staff username or "system"
    scope_summary = models.TextField(blank=True)   # human-readable list of what was deleted

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"DataDestructionCertificate({self.reference_code}, school={self.school_id})"
