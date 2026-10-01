import uuid
from django.conf import settings
from django.db import models
from .experience_models import RevisionQuerySet


class ClassroomAttendanceSession(models.Model):
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    date = models.DateField()
    version = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'section', 'date'], name='unique_attendance_session')]


class ClassroomAttendanceAudit(models.Model):
    session = models.ForeignKey(ClassroomAttendanceSession, on_delete=models.PROTECT, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    changes = models.JSONField(default=list)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        ordering = ['version']
        constraints = [models.UniqueConstraint(fields=['session', 'version'], name='unique_attendance_audit_version')]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Attendance history is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Attendance history is append-only.')


class ClassroomSubstituteGrant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='substitute_grants')
    granted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    instructions = models.TextField()


class ClassroomEmergencySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    title = models.CharField(max_length=160)
    kind = models.CharField(max_length=16, choices=[('drill', 'Drill'), ('incident', 'Incident')])
    started_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    version = models.PositiveIntegerField(default=1)
    completion_note = models.TextField(blank=True)


class ClassroomEmergencyCheck(models.Model):
    session = models.ForeignKey(ClassroomEmergencySession, on_delete=models.PROTECT, related_name='checks')
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT)
    state = models.CharField(max_length=16, default='unknown')
    note = models.TextField(blank=True)
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True)
    checked_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['session', 'student'], name='unique_emergency_student')]


class ClassroomOperationEvent(models.Model):
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
        constraints = [models.UniqueConstraint(fields=['school_id', 'actor', 'request_key'], name='unique_classroom_operation_retry')]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Operational evidence is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Operational evidence is append-only.')
