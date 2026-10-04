"""Restricted school health records referencing canonical student and guardian identity."""
import uuid
from decimal import Decimal
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


def school_date(school, stamp=None):
    try:
        return (stamp or timezone.now()).astimezone(ZoneInfo(school.timezone)).date()
    except (ZoneInfoNotFoundError, ValueError, TypeError):
        raise ValidationError('A valid school timezone is required for clinical dates.')


class RetainedQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError('Health records must be retained; use an audited correction.')

    def update(self, **kwargs):
        raise ValidationError('Use the audited health workflow.')

    def bulk_update(self, *args, **kwargs):
        raise ValidationError('Use the audited health workflow.')

    def bulk_create(self, *args, **kwargs):
        raise ValidationError('Use the audited health workflow.')


class MedicationAuthorization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey('core.School', on_delete=models.PROTECT)
    student = models.ForeignKey('core.Student', on_delete=models.PROTECT)
    guardian = models.ForeignKey('core.Guardian', on_delete=models.PROTECT)
    guardian_authority_verified = models.BooleanField(default=False)
    medication = models.CharField(max_length=160)
    dose = models.DecimalField(max_digits=8, decimal_places=3)
    unit = models.CharField(max_length=24)
    route = models.CharField(max_length=40)
    directions = models.CharField(max_length=2000)
    order_evidence = models.CharField(max_length=300)
    consent_evidence = models.CharField(max_length=300)
    starts_on = models.DateField()
    ends_on = models.DateField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=2000, blank=True)
    version = models.PositiveIntegerField(default=1)
    objects = RetainedQuerySet.as_manager()

    class Meta:
        ordering = ['-created_at', 'id']
        indexes = [models.Index(fields=['school', 'student', 'ends_on'])]

    def clean(self):
        if self.student.school_id != self.school_id or self.guardian.school_id != self.school_id:
            raise ValidationError('Health authorization must remain in its school.')
        if self._state.adding:
            self.validate_current_authority()
        if not self.guardian_authority_verified:
            raise ValidationError('Documented guardian authority verification is required.')
        if not isinstance(self.dose, Decimal) or not self.dose.is_finite() or self.dose <= 0:
            raise ValidationError('A positive documented dose is required.')
        if not isinstance(self.starts_on, date) or not isinstance(self.ends_on, date) or self.ends_on < self.starts_on:
            raise ValidationError('A positive documented dose and valid authorization date range are required.')
        for value in (self.medication, self.unit, self.route, self.directions, self.order_evidence, self.consent_evidence):
            if not value.strip():
                raise ValidationError('Documented order, directions and consent evidence are required.')

    def validate_current_authority(self):
        if self.student.family_id != self.guardian.family_id or self.guardian.custody_flag is not False:
            raise ValidationError('Guardian authority must be verified for this canonical family without an unresolved custody flag.')

    def save(self, *args, **kwargs):
        if not self._state.adding:
            old = type(self).objects.get(pk=self.pk)
            immutable = ['school_id', 'student_id', 'guardian_id', 'guardian_authority_verified', 'medication', 'dose',
                'unit', 'route', 'directions', 'order_evidence', 'consent_evidence', 'starts_on', 'ends_on', 'recorded_by_id']
            if any(getattr(old, field) != getattr(self, field) for field in immutable) or old.revoked_at:
                raise ValidationError('Authorization evidence is immutable; revoke and record a new authorization.')
            if not self.revoked_at or not self.revocation_reason.strip() or self.version != old.version + 1:
                raise ValidationError('Revocation requires its reason and next version.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Health authorization evidence must be retained.')


class HealthEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey('core.School', on_delete=models.PROTECT)
    student = models.ForeignKey('core.Student', on_delete=models.PROTECT)
    kind = models.CharField(max_length=24, choices=[(v, v.title()) for v in ['visit', 'administration', 'immunization', 'care_plan']])
    occurred_at = models.DateTimeField()
    topic = models.CharField(max_length=160)
    summary = models.CharField(max_length=4000)
    follow_up_on = models.DateField(null=True, blank=True)
    evidence_reference = models.CharField(max_length=300, blank=True)
    authorization = models.ForeignKey(MedicationAuthorization, on_delete=models.PROTECT, null=True, blank=True)
    administration_state = models.CharField(max_length=16, blank=True, choices=[(v, v.title()) for v in ['given', 'refused', 'not_given']])
    administered_dose = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    administered_unit = models.CharField(max_length=24, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    corrects = models.OneToOneField('self', on_delete=models.PROTECT, null=True, blank=True, related_name='correction')
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RetainedQuerySet.as_manager()

    class Meta:
        ordering = ['-occurred_at', 'id']
        indexes = [models.Index(fields=['school', 'student', 'occurred_at'])]

    def clean(self):
        from django.utils import timezone
        if self.student.school_id != self.school_id:
            raise ValidationError('Health entry and canonical student must remain in the same school.')
        if not isinstance(self.occurred_at, datetime) or timezone.is_naive(self.occurred_at) or self.occurred_at > timezone.now() or school_date(self.school, self.occurred_at) < self.student.dob:
            raise ValidationError('Event time must be timezone-aware, no later than now, and no earlier than the student birth date.')
        if self.follow_up_on and self.follow_up_on < school_date(self.school, self.occurred_at):
            raise ValidationError('Follow-up cannot precede the recorded event.')
        if self.corrects_id and (self.corrects.school_id != self.school_id or self.corrects.student_id != self.student_id or self.corrects.kind != self.kind):
            raise ValidationError('A correction must retain its school, student and record kind.')
        if self.kind in {'immunization', 'care_plan'} and not self.evidence_reference.strip():
            raise ValidationError('An evidence reference is required for immunization and care-plan records.')
        if self.kind == 'administration':
            order = self.authorization
            if order is None or order.school_id != self.school_id or order.student_id != self.student_id:
                raise ValidationError('Administration requires the same school and student authorization.')
            order.clean()
            order.validate_current_authority()
            if not order.starts_on <= school_date(self.school, self.occurred_at) <= order.ends_on or (order.revoked_at and self.occurred_at >= order.revoked_at):
                raise ValidationError('Authorization must be in effect at the recorded administration time.')
            if self.administration_state not in {'given', 'refused', 'not_given'}:
                raise ValidationError('Record given, refused or not given.')
            if self.administration_state == 'given':
                if self.administered_dose != order.dose or self.administered_unit != order.unit:
                    raise ValidationError('Recorded dose and unit must match the documented authorization; no conversion or dose advice is provided.')
            elif self.administered_dose is not None or self.administered_unit:
                raise ValidationError('A refused/not-given event cannot record an administered dose.')
        elif self.authorization_id or self.administration_state or self.administered_dose is not None or self.administered_unit:
            raise ValidationError('Administration fields belong only to medication administration entries.')

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Health entries are immutable; append a correction.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Health entries must be retained.')


class HealthMutation(models.Model):
    school = models.ForeignKey('core.School', on_delete=models.PROTECT)
    student = models.ForeignKey('core.Student', on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    request_key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    operation = models.CharField(max_length=24)
    result = models.JSONField()
    reason = models.CharField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RetainedQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=['school', 'actor', 'request_key'], name='student_health_retry')]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError('Health mutation evidence is immutable.')
        if self.student.school_id != self.school_id or not self.reason.strip():
            raise ValidationError('Mutation evidence requires the same school and a reason.')
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Health mutation evidence must be retained.')
