from django.conf import settings
from django.db import models
from core.immutable_history import AppendOnlyHistory


class ClassroomSectionPlanning(models.Model):
    school_id = models.UUIDField(db_index=True)
    section = models.OneToOneField('academics.Section', on_delete=models.PROTECT)
    target_size = models.PositiveSmallIntegerField()
    planning_note = models.TextField()
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    version = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)


class ClassroomPlanningEvent(AppendOnlyHistory):
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school_id', 'actor', 'request_key'], name='unique_classroom_planning_retry')]
