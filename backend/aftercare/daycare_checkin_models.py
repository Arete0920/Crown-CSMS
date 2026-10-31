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
    class Meta:
        constraints=[
            models.UniqueConstraint(fields=["school","child","care_date"],name="dia_attendance_child_day_uq"),
            models.UniqueConstraint(fields=["school","request_key"],name="dia_attendance_retry_uq"),
        ]
        indexes=[models.Index(fields=["school","room","care_date"],name="dia_attendance_room_idx")]
    def clean(self):
        super().clean()
        self._require_same_school("site","room","child","program","enrollment","actor")
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
    def save(self,*args,**kwargs):
        if not self._state.adding:
            raise ValidationError("Check-in is immutable; audited release workflow required.")
        return super().save(*args,**kwargs)
