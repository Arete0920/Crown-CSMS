import uuid
from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class SessionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Use validated import session transitions.')

    def bulk_update(self, *args, **kwargs):
        raise ValidationError('Use validated import session transitions.')

    def bulk_create(self, *args, **kwargs):
        raise ValidationError('Use validated import session transitions.')

    def delete(self):
        if self.filter(status__in=['committed', 'verified']).exists():
            raise ValidationError('Committed import evidence must be retained.')
        return super().delete()


class StudentImportWizardSession(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_CONFIGURED = "configured"
    STATUS_PREVIEWED = "previewed"
    STATUS_COMMITTED = "committed"
    STATUS_VERIFIED = "verified"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_CONFIGURED, "Configured"),
        (STATUS_PREVIEWED, "Previewed"),
        (STATUS_COMMITTED, "Committed"),
        (STATUS_VERIFIED, "Verified"),
    ]

    objects = SessionQuerySet.as_manager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(
        "core.School",
        on_delete=models.PROTECT,
        related_name="student_import_wizard_sessions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="+",
    )
    # Column mapping: {"first_name": "col_A", "last_name": "col_B", ...}
    column_map = models.JSONField(default=dict)
    # Raw staged rows from upload: [{"first_name": ..., ...}, ...]
    staged_rows = models.JSONField(default=list)
    # Dry-run results: {"valid": 12, "errors": [...]}
    preview_result = models.JSONField(null=True, blank=True)
    # Final write result: {"created": 10, "updated": 2, "skipped": 0, "errors": [...]}
    commit_result = models.JSONField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"StudentImportWizard {self.id} ({self.status})"

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = type(self).objects.get(pk=self.pk)
            if previous.status in {self.STATUS_COMMITTED, self.STATUS_VERIFIED}:
                retained = ('school_id', 'created_by_id', 'column_map', 'staged_rows', 'preview_result', 'commit_result')
                if any(getattr(previous, key) != getattr(self, key) for key in retained) or self.status not in {previous.status, self.STATUS_VERIFIED}:
                    raise ValidationError('Committed import evidence is retained; start a new reviewed session.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status in {self.STATUS_COMMITTED, self.STATUS_VERIFIED}:
            raise ValidationError('Committed import evidence must be retained.')
        return super().delete(*args, **kwargs)
