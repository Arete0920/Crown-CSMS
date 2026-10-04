"""Versioned content; enrollment and recipient identity remain in their own apps."""
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class ContentRelease(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey('reenrollment.ReenrollmentSession', on_delete=models.PROTECT, related_name='content_releases')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    template_version = models.PositiveIntegerField(default=1, editable=False)
    revision = models.PositiveIntegerField(default=1)
    title = models.CharField(max_length=200)
    blocks = models.JSONField(default=list)
    publish_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, default='draft', choices=[(s, s.title()) for s in ('draft', 'approved', 'published', 'cancelled')])
    approved_fingerprint = models.CharField(max_length=64, blank=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='approved_content_releases')
    published_at = models.DateTimeField(null=True, blank=True)
    snapshot = models.JSONField(default=dict, blank=True)
    last_error = models.CharField(max_length=500, blank=True)
    supersedes = models.ForeignKey('self', null=True, blank=True, on_delete=models.PROTECT, related_name='superseded_by')
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        from .release_services import validate_blocks
        validate_blocks(self.blocks)
        if any(value and timezone.is_naive(value) for value in (self.publish_at, self.expires_at)):
            raise ValidationError("Schedule timestamps must include timezone offsets.")
        if self.publish_at and self.expires_at and self.expires_at <= self.publish_at:
            raise ValidationError('Expiry must follow publication.')
        if self.supersedes_id and self.supersedes.session.school_id != self.session.school_id:
            raise ValidationError('Correction must belong to the same school.')

    def save(self, *args, **kwargs):
        self.full_clean()
        previous = type(self).objects.filter(pk=self.pk).first()
        if previous and previous.status in ('published', 'cancelled'):
            raise ValidationError('Published and cancelled releases are immutable.')
        super().save(*args, **kwargs)


class ReleaseReceipt(models.Model):
    release = models.ForeignKey(ContentRelease, on_delete=models.PROTECT, related_name='receipts')
    guardian = models.ForeignKey('households.Guardian', on_delete=models.PROTECT)
    outbox = models.OneToOneField('comms.OutboxMessage', null=True, blank=True, on_delete=models.PROTECT)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    response = models.CharField(max_length=16, blank=True, choices=[('', 'No response'), ('returning', 'Returning'), ('declining', 'Declining'), ('undecided', 'Undecided')])

    class Meta:
        constraints = [models.UniqueConstraint(fields=['release', 'guardian'], name='unique_release_guardian')]

    def save(self, *args, **kwargs):
        if self.guardian.school_id != self.release.session.school_id:
            raise ValidationError('Recipient must belong to the release school.')
        if self.outbox_id and self.outbox.school_id != str(self.guardian.school_id):
            raise ValidationError('Outbox must belong to the recipient school.')
        self.full_clean()
        super().save(*args, **kwargs)
