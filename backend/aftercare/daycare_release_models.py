"""Append-only Diadem custody event: physical guardian handoff attested by staff.

Government ID numbers/images are deliberately not collected here. This stores
only the evidence method, actor, canonical guardian and event timestamp.
"""
from __future__ import annotations

import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from .daycare_models import DaycareScopedRecord
from .daycare_release_policy import IDENTITY_METHODS


class DaycareRelease(DaycareScopedRecord):
    """One and only one guarded release for a specific check-in event."""

    attendance = models.OneToOneField(
        "aftercare.DaycareAttendance", on_delete=models.PROTECT,
        related_name="custody_release",
    )
    site = models.ForeignKey("aftercare.DaycareSite", on_delete=models.PROTECT, related_name="custody_releases")
    room = models.ForeignKey("aftercare.DaycareRoom", on_delete=models.PROTECT, related_name="custody_releases")
    child = models.ForeignKey("aftercare.DaycareChild", on_delete=models.PROTECT, related_name="custody_releases")
    guardian_authority = models.ForeignKey(
        "aftercare.DaycareGuardianAuthority", on_delete=models.PROTECT,
        related_name="custody_releases",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="daycare_releases_performed",
    )
    released_at = models.DateTimeField()
    identity_method = models.CharField(max_length=32, choices=[
        ("GOVERNMENT_PHOTO_ID", "Government photo ID"),
        ("APPROVED_PHOTO_ROSTER", "Approved photo roster"),
        ("PERSONALLY_KNOWN", "Personally known to releasing staff"),
    ])
    identity_verified = models.BooleanField(default=False)
    guardian_name_snapshot = models.CharField(max_length=180)
    request_key = models.UUIDField(default=uuid.uuid4)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "request_key"], name="dia_release_retry_uq"),
            models.CheckConstraint(condition=models.Q(identity_verified=True), name="dia_release_id_verified_ck"),
            models.CheckConstraint(condition=models.Q(identity_method__in=sorted(IDENTITY_METHODS)), name="dia_release_method_ck"),
        ]
        indexes = [
            models.Index(fields=["school", "room", "released_at"], name="dia_release_room_at_idx"),
            models.Index(fields=["school", "child", "released_at"], name="dia_release_child_at_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school(
            "attendance", "site", "room", "child", "guardian_authority", "actor",
        )
        if (
            self.attendance_id and (
                self.attendance.site_id != self.site_id
                or self.attendance.room_id != self.room_id
                or self.attendance.child_id != self.child_id
                or self.attendance.school_id != self.school_id
            )
        ):
            raise ValidationError("Release must match the original attendance and room.")
        if (
            self.guardian_authority_id
            and (
                self.guardian_authority.child_id != self.child_id
                or self.guardian_authority.guardian.school_id != self.school_id
                or self.guardian_authority.guardian.household_id != self.child.household_id
            )
        ):
            raise ValidationError("Release authority must belong to this child and household.")
        if not self.identity_verified or self.identity_method not in IDENTITY_METHODS:
            raise ValidationError("Releasing staff must attest verified physical identity.")
        if not self.guardian_name_snapshot.strip():
            raise ValidationError("The canonical recipient name must be recorded.")
        if self.released_at is None or timezone.is_naive(self.released_at):
            raise ValidationError("Release timestamp must be timezone-aware.")
        if self.attendance_id and self.released_at < self.attendance.checked_in_at:
            raise ValidationError("Release cannot precede child admission.")
        if self.attendance_id:
            try:
                local_day = timezone.localtime(self.released_at, ZoneInfo(self.school.timezone)).date()
            except (ZoneInfoNotFoundError, TypeError, ValueError) as exc:
                raise ValidationError("Care tenant timezone configuration is invalid.") from exc
            if local_day != self.attendance.care_date:
                raise ValidationError("Overnight release requires a separate governed workflow.")
        if not self.actor_id or not self.actor.is_active:
            raise ValidationError("Active releasing staff required.")
        if self.guardian_authority_id:
            authority = self.guardian_authority
            if not (
                authority.is_active and authority.verified and authority.can_pickup
                and authority.custody_status == "CLEAR" and authority.verified_by.is_active
                and authority.verified_by.school_id == self.school_id
                and authority.verified_at <= self.released_at
            ):
                raise ValidationError("Recipient does not have current verified custody clearance.")
            if (
                (authority.effective_from and self.released_at < authority.effective_from)
                or (authority.effective_until and self.released_at >= authority.effective_until)
            ):
                raise ValidationError("Recipient authority is not effective at release time.")
            guardian = authority.guardian
            if self.guardian_name_snapshot != f"{guardian.first_name} {guardian.last_name}".strip():
                raise ValidationError("Recipient name must come from the authorized guardian record.")

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Custody release records are append-only and cannot be edited.")
        return super().save(*args, **kwargs)
