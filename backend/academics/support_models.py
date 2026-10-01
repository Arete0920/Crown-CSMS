from django.conf import settings
from django.db import models
from .experience_models import RevisionQuerySet


class ClassroomInterventionLink(models.Model):
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    case = models.ForeignKey('signals.InterventionCase', on_delete=models.PROTECT, related_name='classroom_links')

    class Meta:
        constraints = [models.UniqueConstraint(fields=['section', 'case'], name='unique_classroom_intervention')]


class ClassroomRestorativeLink(models.Model):
    school_id = models.UUIDField(db_index=True)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT)
    incident = models.ForeignKey('discipline.DisciplineIncident', on_delete=models.PROTECT, related_name='classroom_links')
    student = models.ForeignKey('households.Student', on_delete=models.PROTECT)
    review_at = models.DateTimeField()
    version = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['section', 'incident'], name='unique_classroom_restorative')]


class ClassroomSupportEvent(models.Model):
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
        constraints = [models.UniqueConstraint(fields=['school_id', 'actor', 'request_key'], name='unique_classroom_support_retry')]

    def save(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        if not self._state.adding:
            raise ValidationError('Support history is append-only.')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError('Support history is append-only.')
