"""Audited, transaction-safe, current-authority guardian handoff for Diadem."""
from __future__ import annotations
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from audit.models import AuditLog
from core.models import School, UserAccount
from core.permissions import user_has_permission
from .daycare_checkin import require_entitlement
from .daycare_checkin_models import DaycareAttendance, DaycareRoomStaffCoverage
from .daycare_models import DaycareRoom, DaycareGuardianAuthority
from .daycare_release_models import DaycareRelease
from .daycare_policy import Child
from .daycare_release_policy import CheckedIn, RecipientAuthority, ReleasingStaff, IDENTITY_METHODS, release_decision

class ReleaseRefused(Exception):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

def release_child(*,school_id:UUID,actor_id:UUID,site_id:UUID,room_id:UUID,
                  attendance_id:UUID,guardian_authority_id:UUID,request_key:UUID,
                  identity_verified:bool,identity_method:str)->DaycareRelease:
    ids=(school_id,actor_id,site_id,room_id,attendance_id,guardian_authority_id,request_key)
    if any(not isinstance(v,UUID) or v.int==0 for v in ids):
        raise ReleaseRefused("invalid_identity")
    if type(identity_verified) is not bool or not identity_verified or identity_method not in IDENTITY_METHODS:
        raise ReleaseRefused("identity_attestation_required")
    try:
        with transaction.atomic():
            school=School.objects.filter(pk=school_id,is_active=True).first()
            actor=UserAccount.objects.filter(pk=actor_id,school_id=school_id,is_active=True).first() if school else None
            if school is None or actor is None:
                raise PermissionDenied("Active Diadem staff tenant required.")
            if not user_has_permission(actor,"diadem.daycare.release",school=school):
                raise PermissionDenied("Explicit custody release permission required.")
            require_entitlement(school_id)
            if DaycareRelease.objects.filter(school=school,request_key=request_key).exists():
                raise ReleaseRefused("request_already_consumed")
            room=DaycareRoom.objects.select_for_update().filter(
                pk=room_id,school=school,site_id=site_id,is_active=True,site__is_active=True).first()
            if room is None:
                raise ReleaseRefused("room_unavailable")
            attendance=DaycareAttendance.objects.select_for_update().filter(
                id=attendance_id,school=school,site_id=site_id,room=room,custody_release__isnull=True).first()
            if attendance is None:
                raise ReleaseRefused("attendance_not_open")
            child=attendance.child
            if not child.is_active or not child.household.is_active or child.site_id!=site_id:
                raise ReleaseRefused("child_unavailable")
            at=timezone.now()
            try:
                day=timezone.localtime(at,ZoneInfo(school.timezone)).date()
            except (TypeError,ValueError,ZoneInfoNotFoundError):
                raise ReleaseRefused("school_timezone_invalid") from None
            authority=DaycareGuardianAuthority.objects.select_for_update().filter(
                pk=guardian_authority_id,school=school,child=child,guardian__school_id=school_id,
                guardian__household_id=child.household_id).first()
            if authority is None:
                raise ReleaseRefused("recipient_not_authorized")
            verified=bool(authority.verified and authority.verified_at<=at and
                          authority.verified_by.is_active and authority.verified_by.school_id==school_id)
            staff_ids=set(DaycareRoomStaffCoverage.objects.filter(
                school=school,site_id=site_id,room=room,is_active=True,is_qualified=True,
                staff__school_id=school_id,staff__is_active=True,
                verified_by__school_id=school_id,verified_by__is_active=True,
                verified_at__isnull=False,verified_at__lte=at,
                starts_at__lte=at,ends_at__gt=at).exclude(qualification_evidence="")
                .values_list("staff_id",flat=True))
            conflicting=set(DaycareRoomStaffCoverage.objects.filter(
                school=school,staff_id__in=staff_ids,is_active=True,
                starts_at__lte=at,ends_at__gt=at).exclude(room=room).values_list("staff_id",flat=True))
            decision=release_decision(
                school_id=school_id,site_id=site_id,actor_id=actor_id,guardian_id=authority.guardian_id,
                child=Child(child.id,school_id,child.household_id,site_id,child.is_active,child.linked_student_id),
                attendance=CheckedIn(school_id,site_id,room.id,child.id,attendance.care_date,attendance.checked_in_at,False),
                staff=ReleasingStaff(school_id,site_id,room.id,actor_id,actor.is_active,
                    actor_id in (staff_ids-conflicting),True),
                authority=RecipientAuthority(school_id,authority.guardian.household_id,
                    child.id,authority.guardian_id,authority.is_active,verified,authority.can_pickup,
                    authority.custody_status,authority.effective_from,authority.effective_until),
                at=at,local_day=day,authenticated=True,
                identity_verified=identity_verified,identity_method=identity_method)
            if not decision.allowed:
                raise ReleaseRefused(decision.code)
            guardian_name=f"{authority.guardian.first_name} {authority.guardian.last_name}".strip()
            record=DaycareRelease.objects.create(school=school,site=room.site,room=room,
                child=child,attendance=attendance,guardian_authority=authority,actor=actor,
                released_at=at,identity_method=identity_method,identity_verified=True,
                guardian_name_snapshot=guardian_name,request_key=request_key)
            AuditLog.objects.create(user_id=actor_id,action="diadem.daycare.release",
                model="DaycareRelease",object_id=str(record.id),
                metadata={"school_id":str(school_id),"site_id":str(site_id),"room_id":str(room_id),
                          "child_id":str(child.id),"attendance_id":str(attendance.id),
                          "guardian_authority_id":str(authority.id),"request_key":str(request_key),
                          "identity_method":identity_method})
            return record
    except IntegrityError as exc:
        raise ReleaseRefused("release_conflict") from exc
