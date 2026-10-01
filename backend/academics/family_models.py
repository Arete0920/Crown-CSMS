import uuid
from django.conf import settings
from django.db import models
from .experience_models import RevisionQuerySet


class ClassroomDisclosure(models.Model):
    """Explicit classroom disclosure restriction; never an inferred custody judgment."""
    school_id = models.UUIDField(db_index=True)
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT)
    guardian = models.ForeignKey('households.Guardian', on_delete=models.PROTECT)
    allowed = models.BooleanField(default=True)
    reason = models.TextField()
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'student', 'guardian'], name='unique_classroom_disclosure')]


class ClassroomNotificationPreference(models.Model):
    school_id = models.UUIDField(db_index=True)
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    in_app = models.BooleanField(default=True)
    digest_day = models.PositiveSmallIntegerField(default=0)
    timezone = models.CharField(max_length=64, default='UTC')
    quiet_start = models.TimeField(null=True, blank=True)
    quiet_end = models.TimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'account'], name='unique_classroom_preferences')]


class ClassroomConferenceSlot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    location = models.CharField(max_length=200)
    state = models.CharField(max_length=20, default='available')

    class Meta:
        ordering = ['starts_at', 'id']


class ClassroomFamilyThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT)
    guardian = models.ForeignKey('households.Guardian', on_delete=models.PROTECT)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    assignment = models.ForeignKey('academics.Assignment', on_delete=models.PROTECT, null=True, blank=True)
    slot = models.OneToOneField(ClassroomConferenceSlot, on_delete=models.PROTECT, null=True, blank=True)
    kind = models.CharField(max_length=20, choices=[(v, v.title()) for v in ['conversation', 'consent', 'conference']])
    title = models.CharField(max_length=160)
    state = models.CharField(max_length=20, default='open')
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', 'id']


class ClassroomFamilyMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(ClassroomFamilyThread, on_delete=models.PROTECT, related_name='messages')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    content = models.TextField()
    decision = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        ordering = ['created_at', 'id']

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Family messages are append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Family messages are append-only.')


class ClassroomFamilyMutation(models.Model):
    school_id = models.UUIDField(db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    operation = models.CharField(max_length=32)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'actor', 'request_key'], name='unique_family_action_retry')]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Family audit history is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Family audit history is append-only.')


class ClassroomFamilyNotice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    thread = models.ForeignKey(ClassroomFamilyThread, on_delete=models.PROTECT, null=True, blank=True)
    source_key = models.CharField(max_length=160)
    title = models.CharField(max_length=160)
    available_at = models.DateTimeField()
    dismissed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'account', 'source_key'], name='unique_family_notice_source')]
