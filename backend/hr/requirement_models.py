"""School requirements referencing canonical staff, with retained review evidence."""
import uuid
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class RequirementQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Use validated staff requirement saves through the audited workflow.')

    def bulk_update(self, *args, **kwargs):
        raise ValidationError('Use validated staff requirement saves through the audited workflow.')

    def bulk_create(self, *args, **kwargs):
        raise ValidationError('Use validated staff requirement saves through the audited workflow.')

    def delete(self):
        raise ValidationError('Retain staff requirement evidence through the audited workflow.')


class StaffRequirement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey('core.School', on_delete=models.PROTECT)
    staff = models.ForeignKey('core.Staff', on_delete=models.PROTECT, related_name='requirements')
    title = models.CharField(max_length=160)
    category = models.CharField(max_length=24, choices=[(v, v.title()) for v in
        ['training', 'certification', 'clearance', 'acknowledgment']])
    due_date = models.DateField()
    completed_on = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    evidence_reference = models.CharField(max_length=300, blank=True)
    version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = RequirementQuerySet.as_manager()

    class Meta:
        ordering = ['due_date', 'id']
        indexes = [models.Index(fields=['school', 'staff', 'due_date'])]

    def clean(self):
        if self.staff.school_id != self.school_id:
            raise ValidationError('Requirement and staff must belong to the same school.')
        if self.completed_on and not self.evidence_reference.strip():
            raise ValidationError('Completion requires an evidence reference.')
        if self.completed_on and self.completed_on > timezone.localdate():
            raise ValidationError('Completion cannot be recorded in the future.')
        if self.valid_until and (not self.completed_on or self.valid_until < self.completed_on):
            raise ValidationError('Expiry must be on or after the recorded completion date.')

    def save(self, *args, **kwargs):
        if not self._state.adding:
            old = type(self).objects.get(pk=self.pk)
            if any(getattr(old, field) != getattr(self, field) for field in ('school_id', 'staff_id', 'title', 'category')):
                raise ValidationError('Requirement ownership and definition are retained; assign a new requirement.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Retain staff requirement evidence; reopen or renew through the workflow.')


class RequirementEventQuerySet(models.QuerySet):
    def update(self, **kwargs):
        raise ValidationError('Staff requirement history is append-only.')

    def delete(self):
        raise ValidationError('Staff requirement history is append-only.')

    def bulk_create(self, *args, **kwargs):
        raise ValidationError('Record staff requirement events through the audited workflow.')

    def bulk_update(self, *args, **kwargs):
        raise ValidationError('Staff requirement history is append-only.')


class StaffRequirementEvent(models.Model):
    school = models.ForeignKey('core.School', on_delete=models.PROTECT)
    requirement = models.ForeignKey(StaffRequirement, on_delete=models.PROTECT, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    action = models.CharField(max_length=24)
    version = models.PositiveIntegerField()
    before = models.JSONField(default=dict, blank=True)
    after = models.JSONField(default=dict)
    reason = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RequirementEventQuerySet.as_manager()

    class Meta:
        ordering = ['created_at', 'id']
        constraints = [models.UniqueConstraint(fields=['school', 'actor', 'request_key'], name='hr_requirement_retry'),
                       models.UniqueConstraint(fields=['requirement', 'version'], name='hr_requirement_event_version')]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Staff requirement history is append-only.')
        if self.requirement.school_id != self.school_id:
            raise ValidationError('Staff requirement history must remain in its school.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Staff requirement history is append-only.')
