import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


NORMAL_STATE_CHOICES = [
    ("EXPECTED_ON_CAMPUS", "Expected on campus"),
    ("ABSENT", "Absent"),
    ("IN_CLASS", "In class"),
    ("IN_TRANSIT", "In transit"),
    ("OFFICE", "Office"),
    ("NURSE", "Nurse"),
    ("ACTIVITY", "Activity"),
    ("ATHLETICS", "Athletics"),
    ("AFTERCARE", "Aftercare"),
    ("DISMISSAL_QUEUED", "Dismissal queued"),
    ("DISMISSAL_STAGING", "Dismissal staging"),
    ("BUS_BOARDED", "Bus boarded"),
    ("RELEASED", "Released"),
    ("KNOWN_OFF_CAMPUS", "Known off campus"),
]

EMERGENCY_STATE_CHOICES = [
    ("ACCOUNTED_FOR", "Accounted for"),
    ("NEEDS_ASSISTANCE", "Needs assistance"),
    ("MEDICAL", "Medical"),
    ("LOCATION_UNCONFIRMED", "Location unconfirmed"),
    ("RELOCATED", "Relocated"),
    ("READY_FOR_REUNIFICATION", "Ready for reunification"),
    ("REUNIFICATION_IN_PROGRESS", "Reunification in progress"),
    ("REUNIFIED", "Reunified"),
]


class AccountabilityState(models.Model):
    """Current operational projection for one canonical student."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    student = models.OneToOneField(
        "households.Student",
        on_delete=models.PROTECT,
        related_name="accountability_state",
    )
    normal_state = models.CharField(
        max_length=40,
        choices=NORMAL_STATE_CHOICES,
        default="EXPECTED_ON_CAMPUS",
    )
    emergency_state = models.CharField(
        max_length=40,
        choices=EMERGENCY_STATE_CHOICES,
        null=True,
        blank=True,
    )
    location_code = models.CharField(max_length=120, blank=True, default="")
    responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accountability_responsibilities",
    )
    expected_destination = models.CharField(max_length=160, blank=True, default="")
    source_domain = models.CharField(max_length=64, default="accountability")
    source_record_id = models.UUIDField(null=True, blank=True)
    version = models.PositiveBigIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["school_id", "normal_state"], name="accountabil_school__4b0a09_idx"),
            models.Index(fields=["school_id", "emergency_state"], name="accountabil_school__6316fb_idx"),
            models.Index(fields=["school_id", "updated_at"], name="accountabil_school__65ec38_idx"),
        ]

    def clean(self):
        errors = {}
        if self.student_id and self.student.school_id != self.school_id:
            errors["student"] = "Student must belong to the same school."
        if (
            self.responsible_user_id
            and self.responsible_user.school_id is not None
            and self.responsible_user.school_id != self.school_id
        ):
            errors["responsible_user"] = "Responsible user must belong to the same school."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("AccountabilityState cannot be hard-deleted.")


class AccountabilityEvent(models.Model):
    """Append-only record of every accountability transition."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school_id = models.UUIDField(db_index=True)
    student = models.ForeignKey(
        "households.Student",
        on_delete=models.PROTECT,
        related_name="accountability_events",
    )
    event_type = models.CharField(max_length=80)
    from_normal_state = models.CharField(max_length=40, blank=True, default="")
    to_normal_state = models.CharField(max_length=40, blank=True, default="")
    from_emergency_state = models.CharField(max_length=40, blank=True, default="")
    to_emergency_state = models.CharField(max_length=40, blank=True, default="")
    location_code = models.CharField(max_length=120, blank=True, default="")
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="accountability_events",
    )
    source_domain = models.CharField(max_length=64, default="accountability")
    source_record_id = models.UUIDField(null=True, blank=True)
    context = models.JSONField(default=dict, blank=True)
    state_version = models.PositiveBigIntegerField()
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["occurred_at", "id"]
        indexes = [
            models.Index(fields=["school_id", "student", "occurred_at"], name="accountabil_school__55f3fd_idx"),
            models.Index(fields=["school_id", "event_type", "occurred_at"], name="accountabil_school__b39435_idx"),
        ]

    def clean(self):
        errors = {}
        if self.student_id and self.student.school_id != self.school_id:
            errors["student"] = "Student must belong to the same school."
        if (
            self.actor_user_id
            and self.actor_user.school_id is not None
            and self.actor_user.school_id != self.school_id
        ):
            errors["actor_user"] = "Actor user must belong to the same school."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if self.pk and AccountabilityEvent.objects.filter(pk=self.pk).exists():
            raise RuntimeError("AccountabilityEvent is append-only and cannot be updated.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("AccountabilityEvent is append-only and cannot be deleted.")
