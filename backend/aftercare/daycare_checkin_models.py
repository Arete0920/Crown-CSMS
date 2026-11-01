"""Daycare staffing coverage and immutable check-in storage, independent of K12 attendance."""
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from .daycare_models import DaycareScopedRecord

class DaycareRoomStaffCoverage(DaycareScopedRecord):
    site = models.ForeignKey("aftercare.DaycareSite",on_delete=models.PROTECT,related_name="staff_coverage")
    room = models.ForeignKey("aftercare.DaycareRoom",on_delete=models.PROTECT,related_name="staff_coverage")
    staff = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="daycare_coverage")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_qualified = models.BooleanField(default=False)
    qualification_evidence = models.CharField(max_length=255,blank=True,default="")
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,null=True,blank=True,related_name="daycare_coverage_verifications")
    verified_at = models.DateTimeField(null=True,blank=True)
    is_active = models.BooleanField(default=False)
    class Meta:
        constraints=[models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")),name="dia_coverage_window_ck")]
        indexes=[models.Index(fields=["school","room","starts_at"],name="dia_coverage_room_idx")]
    def clean(self):
        super().clean()
        self._require_same_school("site","room","staff","verified_by")
        if self.site_id and self.room_id and self.room.site_id != self.site_id:
            raise ValidationError("Coverage room and site mismatch.")
        for value in (self.starts_at,self.ends_at,self.verified_at):
            if value is not None and timezone.is_naive(value):
                raise ValidationError("Coverage timestamps must be timezone-aware.")
        if self.starts_at and self.ends_at and self.starts_at >= self.ends_at:
            raise ValidationError("Coverage must have positive duration.")
        if self.is_active and not (self.site.is_active and self.room.is_active and self.staff.is_active
            and self.is_qualified and self.qualification_evidence.strip()
            and self.verified_by_id and self.verified_at and self.verified_by.is_active
            and self.verified_by_id != self.staff_id):
            raise ValidationError("Verified independent qualification and active staffing required.")

    def save(self, *args, **kwargs):
        # All changes, including revocation of coverage, must use the same
        # canonical staff-account lock that check-in and release hold before
        # making a ratio / staff authority decision.
        with transaction.atomic():
            if not self._state.adding:
                previous = type(self).objects.select_for_update().filter(
                    pk=self.pk
                ).values("school_id", "site_id", "room_id", "staff_id").first()
                if previous is None:
                    raise ValidationError("Staffing coverage no longer exists.")
                if any(getattr(self, field) != previous[field] for field in previous):
                    raise ValidationError(
                        "Staffing coverage identity is immutable; deactivate and create a new shift."
                    )
            staff = get_user_model().objects.select_for_update().filter(
                pk=self.staff_id, school_id=self.school_id
            ).first()
            if staff is None or (self.is_active and not staff.is_active):
                raise ValidationError("Same-tenant staff must be active for live coverage.")
            if (self.is_active and self.starts_at is not None and
                self.ends_at is not None and
                type(self).objects.filter(
                    school_id=self.school_id, staff_id=self.staff_id,
                    is_active=True, starts_at__lt=self.ends_at,
                    ends_at__gt=self.starts_at,
                ).exclude(pk=self.pk).exists()):
                raise ValidationError(
                    "A staff member cannot have overlapping active room coverage."
                )
            return super().save(*args, **kwargs)

class DaycareAttendance(DaycareScopedRecord):
    site=models.ForeignKey("aftercare.DaycareSite",on_delete=models.PROTECT,related_name="daycare_attendance")
    room=models.ForeignKey("aftercare.DaycareRoom",on_delete=models.PROTECT,related_name="daycare_attendance")
    child=models.ForeignKey("aftercare.DaycareChild",on_delete=models.PROTECT,related_name="daycare_attendance")
    program=models.ForeignKey("aftercare.DaycareProgram",on_delete=models.PROTECT,related_name="daycare_attendance")
    enrollment=models.ForeignKey("aftercare.DaycareEnrollment",on_delete=models.PROTECT,related_name="daycare_attendance")
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="daycare_checkins")
    care_date=models.DateField(db_index=True)
    checked_in_at=models.DateTimeField()
    request_key=models.UUIDField(default=uuid.uuid4)
    # A visit is an immutable admission-to-release custody episode. Historical
    # records all remain visit 1; a new same-day episode needs director approval.
    visit_number=models.PositiveIntegerField(default=1,editable=False)
    reentry_approval=models.OneToOneField(
        "aftercare.DaycareReentryAuthorization",on_delete=models.PROTECT,
        null=True,blank=True,related_name="admitted_visit")
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["school","child","care_date","visit_number"],name="dia_attendance_visit_uq"),
            models.UniqueConstraint(fields=["school","request_key"],name="dia_attendance_retry_uq"),
        ]
        indexes=[models.Index(fields=["school","room","care_date"],name="dia_attendance_room_idx")]
    def clean(self):
        super().clean()
        self._require_same_school("site","room","child","program","enrollment","actor","reentry_approval")
        if (self.site_id and self.room_id and self.room.site_id != self.site_id
            or self.site_id and self.child_id and self.child.site_id != self.site_id
            or self.site_id and self.program_id and self.program.site_id != self.site_id
            or self.enrollment_id and (self.enrollment.child_id != self.child_id
                or self.enrollment.program_id != self.program_id
                or self.enrollment.room_id != self.room_id
                or self.enrollment.site_id != self.site_id)):
            raise ValidationError("Attendance references are not from one care enrollment.")
        if self.checked_in_at and timezone.is_naive(self.checked_in_at):
            raise ValidationError("Check-in time must be timezone-aware.")
        if type(self.visit_number) is not int or self.visit_number < 1:
            raise ValidationError("Custody visit number must be a positive integer.")
        if self.visit_number == 1 and self.reentry_approval_id is not None:
            raise ValidationError("First check-in cannot consume re-entry approval.")
        if self.visit_number > 1:
            if not self.reentry_approval_id:
                raise ValidationError("Re-entry requires a stored director authorization.")
            approval=self.reentry_approval
            previous=approval.previous_attendance
            if (approval.school_id!=self.school_id or approval.site_id!=self.site_id
                or approval.child_id!=self.child_id or approval.care_date!=self.care_date
                or previous.visit_number+1!=self.visit_number
                or previous.school_id!=self.school_id or previous.child_id!=self.child_id
                or previous.site_id!=self.site_id or approval.director_id==self.actor_id
                or self.checked_in_at is None or not (approval.approved_at<=self.checked_in_at<approval.expires_at)
                or not hasattr(previous,"custody_release")):
                raise ValidationError("Re-entry approval does not match this released visit.")
    def save(self,*args,**kwargs):
        if not self._state.adding:
            raise ValidationError("Check-in is immutable; audited release workflow required.")
        return super().save(*args,**kwargs)


class DaycareReentryAuthorization(DaycareScopedRecord):
    """Append-only, short-lived director authorization for one prior released visit.

    This is not a release event, a custody override, or a replacement for
    active enrollment, guardian clearance, staff coverage and room policy.
    The next attendance links to this record through a unique OneToOne key.
    """
    REASONS=[
        ("SCHEDULED_RETURN","Scheduled same-day return"),
        ("DIRECTOR_REVIEWED","Director-reviewed same-day exception"),
    ]
    site=models.ForeignKey("aftercare.DaycareSite",on_delete=models.PROTECT,related_name="reentry_authorizations")
    child=models.ForeignKey("aftercare.DaycareChild",on_delete=models.PROTECT,related_name="reentry_authorizations")
    previous_attendance=models.ForeignKey(
        "aftercare.DaycareAttendance",on_delete=models.PROTECT,related_name="subsequent_reentry_authorizations")
    director=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.PROTECT,related_name="diadem_reentry_authorizations")
    care_date=models.DateField()
    reason_code=models.CharField(max_length=24,choices=REASONS)
    approved_at=models.DateTimeField()
    expires_at=models.DateTimeField()
    request_key=models.UUIDField(default=uuid.uuid4)
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["school","request_key"],name="dia_reentry_request_uq"),
            models.CheckConstraint(condition=models.Q(expires_at__gt=models.F("approved_at")),
                                   name="dia_reentry_window_ck"),
        ]
        indexes=[models.Index(fields=["school","child","care_date"],name="dia_reentry_child_day_idx")]

    def clean(self):
        super().clean()
        self._require_same_school("site","child","previous_attendance","director")
        previous=self.previous_attendance
        if (previous.child_id!=self.child_id or previous.site_id!=self.site_id
            or previous.care_date!=self.care_date or self.child.site_id!=self.site_id):
            raise ValidationError("Director re-entry authorization must match the prior custody visit.")
        if (not self.director.is_active or not self.director.roles.filter(
            school_id=self.school_id,role_code="DAYCARE_DIRECTOR").exists()):
            raise ValidationError("Active, explicitly assigned Diadem director required.")
        if (self.approved_at is None or self.expires_at is None
            or timezone.is_naive(self.approved_at) or timezone.is_naive(self.expires_at)
            or self.expires_at<=self.approved_at):
            raise ValidationError("Re-entry authorization requires a valid aware expiry window.")
        from .daycare_release_models import DaycareRelease
        if not DaycareRelease.objects.filter(
            school_id=self.school_id,attendance_id=self.previous_attendance_id
        ).exists():
            raise ValidationError("Director cannot authorize an unreleased custody visit.")

    def save(self,*args,**kwargs):
        if not self._state.adding:
            raise ValidationError("Director re-entry authorization is append-only.")
        return super().save(*args,**kwargs)
