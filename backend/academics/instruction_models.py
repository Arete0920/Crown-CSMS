import uuid
from django.conf import settings
from django.db import models
from .experience_models import RevisionQuerySet


class ClassroomRubric(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    title = models.CharField(max_length=160)
    criteria = models.JSONField(default=list)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Reuse a rubric or create a new revision; existing criteria are immutable.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Rubric evidence is immutable.')


class ClassroomDeadlineAdjustment(models.Model):
    school_id = models.UUIDField(db_index=True)
    assignment = models.ForeignKey('academics.Assignment', on_delete=models.PROTECT, related_name='deadline_adjustments')
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT)
    due_date = models.DateField()
    instructions = models.TextField()
    reason_private = models.TextField()
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'assignment', 'student'], name='unique_classroom_deadline')]


class ClassroomInstructionEvent(models.Model):
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    operation = models.CharField(max_length=32)
    payload = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'actor', 'request_key'], name='unique_classroom_instruction_retry')]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Instruction history is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Instruction history is append-only.')


class ClassroomMasteryEvidence(models.Model):
    school_id = models.UUIDField(db_index=True)
    record = models.ForeignKey('academics.MasteryRecord', on_delete=models.PROTECT, related_name='classroom_history')
    assignment = models.ForeignKey('academics.Assignment', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    level = models.PositiveSmallIntegerField()
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        ordering = ['created_at', 'id']

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Mastery evidence is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Mastery evidence is append-only.')
