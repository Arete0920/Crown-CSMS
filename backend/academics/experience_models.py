"""Append-only history for canonical academic submissions."""
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class RevisionQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Submission history is append-only.')

    def delete(self):
        raise ValidationError('Submission history is append-only.')


class SubmissionRevision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey('academics.Submission', on_delete=models.PROTECT, related_name='revisions')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    sequence = models.PositiveIntegerField()
    action = models.CharField(max_length=20)
    content = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        ordering = ['sequence']
        constraints = [models.UniqueConstraint(fields=['submission', 'request_key'], name='unique_submission_retry'),
                       models.UniqueConstraint(fields=['submission', 'sequence'], name='unique_submission_revision')]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Submission history is append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Submission history is append-only.')
