"""Transaction-safe Diadem check-in: source-only, release workflow still pending."""
from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from core.models import School, UserAccount
from core.permissions import user_has_permission
from subscriptions.models import Feature, TenantSubscription
from subscriptions.services import EntitlementsService
from audit.models import AuditLog
from .daycare_models import DaycareRoom, DaycareChild, DaycareEnrollment, DaycareGuardianAuthority
from .daycare_checkin_models import DaycareAttendance, DaycareRoomStaffCoverage
from .daycare_policy import Child, CareEnrollment, StaffGrant, RoomPolicy, RoomOccupancy, checkin_decision

class CheckinRefused(Exception):
    def __init__(self,code):
        self.code=code
        super().__init__(code)

def require_entitlement(school_id):
    try:
        subscription=EntitlementsService.get_active_subscription(school_id)
        if not subscription.plan.is_active or subscription.started_at > timezone.now():
            raise PermissionError("Inactive subscription")
        EntitlementsService.assert_enabled(school_id,"diadem.daycare")
    except (PermissionError,Feature.DoesNotExist,TenantSubscription.DoesNotExist,
            TenantSubscription.MultipleObjectsReturned):
        raise PermissionDenied("Diadem Daycare entitlement required.") from None

def checkin_child(*,school_id:UUID,actor_id:UUID,site_id:UUID,room_id:UUID,
                  child_id:UUID,program_code:str,request_key:UUID):
    """Always recheck under DB room lock; no occupancy numbers from the client."""
    if any(not isinstance(v,UUID) or not v.int for v in
           (school_id,actor_id,site_id,room_id,child_id,request_key)):
        raise CheckinRefused("invalid_identity")
    if program_code not in {"DAYCARE","PRESCHOOL"}:
        raise CheckinRefused("invalid_program")
    try:
        with transaction.atomic():
            school=School.objects.filter(pk=school_id,is_active=True).first()
            actor=UserAccount.objects.filter(pk=actor_id,school_id=school_id,is_active=True).first()
            if school is None or actor is None:
                raise PermissionDenied("Diadem staff tenant required.")
            if not user_has_permission(actor,"diadem.daycare.checkin",school=school):
                raise PermissionDenied("Diadem check-in role required.")
            require_entitlement(school_id)
            room=DaycareRoom.objects.select_for_update().select_related("site","policy_verified_by").filter(
                pk=room_id,school=school,site_id=site_id,is_active=True,site__is_active=True).first()
            if room is None:
                raise CheckinRefused("room_unavailable")
            child=DaycareChild.objects.select_for_update().select_related("household").filter(
                pk=child_id,school=school,site_id=site_id,is_active=True,household__is_active=True).first()
            if child is None:
                raise CheckinRefused("child_unavailable")
            at=timezone.now()
            if (room.licensed_capacity is None or room.max_children_per_staff is None or
                    not room.policy_source.strip() or room.policy_verified_at is None or
                    room.policy_verified_at > at or not room.policy_verified_by_id or
                    not room.policy_verified_by.is_active or room.policy_verified_by.school_id != school_id):
                raise CheckinRefused("room_policy_unverified")
            try:
                day=timezone.localtime(at,ZoneInfo(school.timezone)).date()
            except (TypeError,ValueError,ZoneInfoNotFoundError):
                raise CheckinRefused("school_timezone_invalid") from None
            enrollments=list(DaycareEnrollment.objects.select_for_update().select_related("program").filter(
                school=school,site_id=site_id,room=room,child=child,status="ACTIVE",readiness="READY",
                program__code=program_code,program__is_active=True,start_date__lte=day
            ).filter(Q(end_date__isnull=True)|Q(end_date__gte=day))[:2])
            if len(enrollments)!=1:
                raise CheckinRefused("eligible_enrollment_required")
            enrollment=enrollments[0]
            verified_pickup=DaycareGuardianAuthority.objects.filter(
                school=school,child=child,guardian__school_id=school_id,
                guardian__household_id=child.household_id,verified_by__school_id=school_id,
                verified_by__is_active=True,verified_at__isnull=False,verified_at__lte=at,
                is_active=True,can_pickup=True,custody_status="CLEAR"
            ).filter(Q(effective_from__isnull=True)|Q(effective_from__lte=at),
                     Q(effective_until__isnull=True)|Q(effective_until__gt=at)).exists()
            if not verified_pickup:
                raise CheckinRefused("verified_pickup_authority_required")
            staff_ids=list(DaycareRoomStaffCoverage.objects.filter(
                school=school,site_id=site_id,room=room,is_active=True,is_qualified=True,
                staff__school_id=school_id,staff__is_active=True,
                verified_by__school_id=school_id,verified_by__is_active=True,
                verified_at__isnull=False,verified_at__lte=at,starts_at__lte=at,ends_at__gt=at
            ).exclude(qualification_evidence="").values_list("staff_id",flat=True).distinct())
            if actor_id not in staff_ids:
                raise CheckinRefused("room_staff_authority_required")
            occupied=DaycareAttendance.objects.filter(school=school,room=room,custody_release__isnull=True).count()
            already=DaycareAttendance.objects.filter(school=school,child=child,custody_release__isnull=True).exists()
            if not already and DaycareAttendance.objects.filter(school=school,child=child,care_date=day).exists():
                raise CheckinRefused("repeat_same_day_requires_review")
            decision=checkin_decision(
                school_id=school_id,site_id=site_id,program_code=program_code,local_date=day,
                child=Child(child.id,school_id,child.household_id,site_id,child.is_active,child.linked_student_id),
                staff=StaffGrant(school_id,site_id,actor.is_active,True),
                enrollment=CareEnrollment(school_id,site_id,child.id,enrollment.program.code,
                    enrollment.status,enrollment.readiness,enrollment.start_date,
                    enrollment.end_date,tuple(enrollment.weekdays)),
                room=RoomPolicy(school_id,site_id,room.is_active,
                    room.licensed_capacity,room.max_children_per_staff),
                occupancy=RoomOccupancy(occupied,len(staff_ids),already),
            )
            if not decision.allowed:
                raise CheckinRefused(decision.code)
            record=DaycareAttendance.objects.create(
                school=school,site=room.site,room=room,child=child,program=enrollment.program,
                enrollment=enrollment,actor=actor,care_date=day,checked_in_at=at,request_key=request_key)
            AuditLog.objects.create(user_id=actor_id,action="diadem.daycare.checkin",
                model="DaycareAttendance",object_id=str(record.id),
                metadata={"school_id":str(school_id),"site_id":str(site_id),
                    "room_id":str(room_id),"child_id":str(child_id),"request_key":str(request_key)})
            return record
    except IntegrityError as exc:
        raise CheckinRefused("checkin_conflict") from exc
