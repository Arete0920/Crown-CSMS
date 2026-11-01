"""Standalone Diadem childcare persistence; complements, never replaces, Aftercare.

No authenticated endpoint is exposed by these tables. Tenant-aware services must
resolve the authenticated school and enforce grants before reading/writing rows.
Cross-table tenancy is validated on normal ORM saves. Bulk updates/deletes
are deliberately blocked: SQL foreign keys cannot compare tenant ownership.
Raw SQL and fixture loaders remain privileged operations requiring review.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.utils import timezone


class DaycareProtectedQuerySet(models.QuerySet):
    """Block unvalidated bulk mutations of custody and site-safety records."""

    def delete(self):
        raise ValidationError("Use a governed retention workflow for childcare records.")

    def update(self, **kwargs):
        raise ValidationError("Bulk childcare updates bypass tenant and custody checks.")

    def bulk_create(self, objs, **kwargs):
        raise ValidationError("Bulk childcare inserts bypass tenant and custody checks.")

    def bulk_update(self, objs, fields, **kwargs):
        raise ValidationError("Bulk childcare updates bypass tenant and custody checks.")


class DaycareScopedRecord(models.Model):
    """Childcare-only records are still owned by CROWN's canonical tenant."""

    objects = DaycareProtectedQuerySet.as_manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey("core.School", on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def _require_same_school(self, *relation_names):
        for name in relation_names:
            if getattr(self, f"{name}_id", None) is None:
                continue
            try:
                obj = getattr(self, name)
            except ObjectDoesNotExist as exc:
                raise ValidationError({name: "Referenced record does not exist."}) from exc
            if obj.school_id != self.school_id:
                raise ValidationError({name: "Record belongs to another tenant."})

    def save(self, *args, **kwargs):
        if kwargs.get("raw"):
            raise ValidationError("Raw childcare writes are not permitted.")
        self.full_clean()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Childcare records require governed retention, not hard deletion.")


class DaycareSite(DaycareScopedRecord):
    """A standalone center or a care location attached to a CROWN school."""

    code = models.SlugField(max_length=48)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["school", "code"], name="dia_site_school_code_uq"),
        ]
        indexes = [
            models.Index(fields=["school", "is_active"], name="dia_site_school_active_idx"),
        ]


class DaycareRoom(DaycareScopedRecord):
    """A care room with *verified* local policy, not assumed K-12 ratios."""

    site = models.ForeignKey(DaycareSite, on_delete=models.PROTECT, related_name="care_rooms")
    code = models.SlugField(max_length=48)
    name = models.CharField(max_length=160)
    licensed_capacity = models.PositiveIntegerField(null=True, blank=True)
    max_children_per_staff = models.PositiveIntegerField(null=True, blank=True)
    policy_source = models.CharField(max_length=255, blank=True, default="")
    policy_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="daycare_room_policy_approvals",
    )
    policy_verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "code"], name="dia_room_site_code_uq"),
            models.CheckConstraint(
                condition=models.Q(licensed_capacity__isnull=True) | models.Q(licensed_capacity__gt=0),
                name="dia_room_capacity_positive_ck",
            ),
            models.CheckConstraint(
                condition=models.Q(max_children_per_staff__isnull=True) | models.Q(max_children_per_staff__gt=0),
                name="dia_room_ratio_positive_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "site", "is_active"], name="dia_room_school_site_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school("site")
        if self.is_active:
            if (not self.site.is_active or not self.licensed_capacity or
                    not self.max_children_per_staff or not self.policy_source.strip() or
                    not self.policy_verified_by_id or not self.policy_verified_at):
                raise ValidationError("Activation needs an active site and documented ratio/capacity approval.")
            if (self.policy_verified_by.school_id != self.school_id or
                    not self.policy_verified_by.is_active):
                raise ValidationError("Ratio approver must be an active user from this tenant.")
            if timezone.is_naive(self.policy_verified_at):
                raise ValidationError("Ratio approval timestamp must be timezone-aware.")


class DaycareChild(DaycareScopedRecord):
    """Early-childhood identity independent of any K-12 Student record."""

    site = models.ForeignKey(DaycareSite, on_delete=models.PROTECT, related_name="care_children")
    household = models.ForeignKey("households.Household", on_delete=models.PROTECT, related_name="daycare_children")
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    date_of_birth = models.DateField()
    linked_student = models.ForeignKey(
        "households.Student", on_delete=models.PROTECT, null=True, blank=True,
        related_name="daycare_profiles",
    )
    is_active = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=["school", "site", "is_active"], name="dia_child_school_site_idx"),
            models.Index(fields=["school", "household"], name="dia_child_household_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school("site", "household", "linked_student")
        if self.date_of_birth and self.date_of_birth > timezone.localdate():
            raise ValidationError({"date_of_birth": "Future birth dates are not valid."})
        if (self.linked_student_id is not None and
                self.linked_student.household_id != self.household_id):
            raise ValidationError({"linked_student": "K-12 student must share the household."})
        if self.is_active and (not self.site.is_active or not self.household.is_active):
            raise ValidationError("A child cannot be active in an inactive site or household.")


class DaycareGuardianAuthority(DaycareScopedRecord):
    """Explicit per-child clearance; household membership is not custody authority."""

    CUSTODY = [("UNKNOWN", "Unknown"), ("CLEAR", "Clear"), ("RESTRICTED", "Restricted")]
    child = models.ForeignKey(DaycareChild, on_delete=models.PROTECT, related_name="guardian_authorities")
    guardian = models.ForeignKey("households.Guardian", on_delete=models.PROTECT, related_name="daycare_authorities")
    is_active = models.BooleanField(default=False)
    can_view = models.BooleanField(default=False)
    can_pickup = models.BooleanField(default=False)
    custody_status = models.CharField(max_length=12, choices=CUSTODY, default="UNKNOWN")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True,
        related_name="daycare_guardian_verifications",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    effective_from = models.DateTimeField(null=True, blank=True)
    effective_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["child", "guardian"], name="dia_guard_child_guard_uq"),
            models.CheckConstraint(
                condition=(models.Q(effective_from__isnull=True) |
                           models.Q(effective_until__isnull=True) |
                           models.Q(effective_until__gt=models.F("effective_from"))),
                name="dia_guard_window_order_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "child", "is_active"], name="dia_guard_school_child_idx"),
        ]

    @property
    def verified(self):
        return self.verified_by_id is not None and self.verified_at is not None

    def clean(self):
        super().clean()
        self._require_same_school("child", "guardian")
        if self.child_id and self.guardian_id and self.child.household_id != self.guardian.household_id:
            raise ValidationError("Authority must match the child's household.")
        if (self.verified_by_id is None) != (self.verified_at is None):
            raise ValidationError("Guardian verification needs both approver and timestamp.")
        if self.verified_by_id is not None:
            if self.verified_by.school_id != self.school_id or not self.verified_by.is_active:
                raise ValidationError("Guardian verifier must be an active user from this tenant.")
        for value in (self.verified_at, self.effective_from, self.effective_until):
            if value is not None and timezone.is_naive(value):
                raise ValidationError("Authorization timestamps must be timezone-aware.")
        if (self.effective_from and self.effective_until and
                self.effective_from >= self.effective_until):
            raise ValidationError("Guardian authority has an invalid effective window.")
        if self.is_active and (not self.verified or self.custody_status != "CLEAR"):
            raise ValidationError("Active authority requires verified, clear custody status.")


class DaycareProgram(DaycareScopedRecord):
    """Program identities remain separate from AM/PM Extended Care and Camp."""

    TYPES = [("DAYCARE", "Daycare"), ("PRESCHOOL", "Preschool")]
    site = models.ForeignKey(DaycareSite, on_delete=models.PROTECT, related_name="care_programs")
    code = models.CharField(max_length=20, choices=TYPES)
    name = models.CharField(max_length=160)
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "code"], name="dia_program_site_code_uq"),
        ]
        indexes = [
            models.Index(fields=["school", "site", "is_active"], name="dia_prog_school_site_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school("site")
        if self.is_active and not self.site.is_active:
            raise ValidationError("Cannot activate a program in an inactive site.")


class DaycareEnrollment(DaycareScopedRecord):
    """Care enrollment independent of K-12 enrollment; fail-closed by default."""

    STATUSES = [("WAITLISTED", "Waitlisted"), ("ACTIVE", "Active"),
                ("CANCELLED", "Cancelled"), ("EXPIRED", "Expired")]
    READINESS = [("INCOMPLETE", "Incomplete"), ("BLOCKED", "Blocked"), ("READY", "Ready")]
    site = models.ForeignKey(DaycareSite, on_delete=models.PROTECT, related_name="care_enrollments")
    child = models.ForeignKey(DaycareChild, on_delete=models.PROTECT, related_name="care_enrollments")
    program = models.ForeignKey(DaycareProgram, on_delete=models.PROTECT, related_name="care_enrollments")
    room = models.ForeignKey(DaycareRoom, on_delete=models.PROTECT, null=True, blank=True,
                             related_name="care_enrollments")
    status = models.CharField(max_length=12, choices=STATUSES, default="WAITLISTED")
    readiness = models.CharField(max_length=12, choices=READINESS, default="INCOMPLETE")
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    weekdays = models.JSONField(default=list)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["child", "program", "start_date"], name="dia_enroll_child_start_uq"),
            models.CheckConstraint(
                condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")),
                name="dia_enroll_dates_order_ck",
            ),
        ]
        indexes = [
            models.Index(fields=["school", "site", "status"], name="dia_enroll_school_site_idx"),
            models.Index(fields=["school", "child"], name="dia_enroll_school_child_idx"),
        ]

    def clean(self):
        super().clean()
        self._require_same_school("site", "child", "program", "room")
        if (self.child_id and self.child.site_id != self.site_id or
                self.program_id and self.program.site_id != self.site_id or
                self.room_id and self.room.site_id != self.site_id):
            raise ValidationError("Child, room and program must belong to the same site.")
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date precedes start date.")
        if (not isinstance(self.weekdays, list) or len(self.weekdays) > 7 or
                len(set(map(str, self.weekdays))) != len(self.weekdays) or
                any(type(day) is not int or not 0 <= day <= 6 for day in self.weekdays)):
            raise ValidationError("Weekdays must be unique integers in 0..6.")
        if self.status == "ACTIVE" and self.readiness == "READY":
            if not self.weekdays or self.room_id is None:
                raise ValidationError("Ready enrollment needs scheduled weekdays and a care room.")
            if not (self.child.is_active and self.program.is_active and
                    self.site.is_active and self.room.is_active):
                raise ValidationError("Ready enrollment needs active child, program, site and room.")
