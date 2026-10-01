"""Classroom collaboration records; not substitutes for grades or clinical records."""
import uuid
from django.conf import settings
from django.db import models
from .experience_models import RevisionQuerySet

KINDS = ['announcement', 'home_support', 'practice', 'formative_check', 'group_project', 'positive_observation',
         'accommodation', 'support_plan', 'service', 'resource', 'coaching', 'interruption',
         'help_request', 'goal', 'reflection', 'portfolio', 'absence_explanation', 'family_service']


class ClassroomRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT, related_name='classroom_records')
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT, null=True, blank=True)
    kind = models.CharField(max_length=32, choices=[(v, v.replace('_', ' ').title()) for v in KINDS])
    title = models.CharField(max_length=160)
    body = models.TextField()
    visibility = models.CharField(max_length=16, choices=[(v, v.title()) for v in ['class', 'family', 'staff', 'private']])
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_classroom_records')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    due_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    state = models.CharField(max_length=16, default='open')
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'created_by', 'request_key'], name='unique_classroom_record_retry')]
        indexes = [models.Index(fields=['school_id', 'section', 'state'])]
        ordering = ['-created_at', 'id']


class ClassroomResponse(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(ClassroomRecord, on_delete=models.PROTECT, related_name='responses')
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    content = models.TextField()
    feedback = models.TextField(blank=True)
    state = models.CharField(max_length=20, default='submitted')
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['record', 'student'], name='unique_classroom_response')]


class ClassroomEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    record = models.ForeignKey(ClassroomRecord, on_delete=models.PROTECT, related_name='events')
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT, null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    action = models.CharField(max_length=32)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['record', 'request_key'], name='unique_classroom_event_retry')]
        ordering = ['created_at', 'id']

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Classroom history is append-only.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Classroom history is append-only.')
