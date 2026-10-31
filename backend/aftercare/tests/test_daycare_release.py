"""Synthetic DB-backed custody handoff regression tests; not a PostgreSQL lock test."""
from datetime import timedelta
from uuid import uuid4
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from aftercare.daycare_checkin import CheckinRefused
from aftercare.daycare_release import ReleaseRefused,release_child
from aftercare.models import DaycareRelease,DaycareAttendance
from audit.models import AuditLog
from core.models import School,UserAccount
from .test_daycare_checkin import setup,check
pytestmark=pytest.mark.django_db

def release(d,attendance,**overrides):
    params=dict(school_id=d["school"].id,actor_id=d["actor"].id,site_id=d["site"].id,
        room_id=d["room"].id,attendance_id=attendance.id,
        guardian_authority_id=d["authority"].id,request_key=uuid4(),
        identity_verified=True,identity_method="GOVERNMENT_PHOTO_ID")
    params.update(overrides)
    return release_child(**params)

def test_release_atomic_audit_and_duplicate_denied():
    d=setup(); attendance=check(d); event=release(d,attendance)
    assert event.attendance_id==attendance.id
    assert event.guardian_name_snapshot=="Synthetic Guardian"
    assert AuditLog.objects.filter(action="diadem.daycare.release",object_id=str(event.id)).count()==1
    with pytest.raises(ValidationError): event.save()
    with pytest.raises(ValidationError): event.delete()
    with pytest.raises(ReleaseRefused) as error: release(d,attendance)
    assert error.value.code=="attendance_not_open"
    assert DaycareRelease.objects.count()==1

@pytest.mark.parametrize("gate",["no_attestation","unknown_method","revoked_guardian",
    "pickup_prohibited","restricted_custody","expired_grant","staff_off_shift","staff_unqualified"])
def test_unsafe_release_denied_without_write(gate):
    d=setup(); attendance=check(d); params={}
    if gate=="no_attestation": params["identity_verified"]=False
    elif gate=="unknown_method": params["identity_method"]="SELF_ATTESTED"
    elif gate=="revoked_guardian": d["authority"].is_active=False; d["authority"].save()
    elif gate=="pickup_prohibited": d["authority"].can_pickup=False; d["authority"].save()
    elif gate=="restricted_custody":
        d["authority"].is_active=False; d["authority"].custody_status="RESTRICTED";d["authority"].save()
    elif gate=="expired_grant":
        d["authority"].effective_until=timezone.now()-timedelta(seconds=1);d["authority"].save()
    elif gate=="staff_off_shift": d["coverage"].is_active=False;d["coverage"].save()
    elif gate=="staff_unqualified":
        d["coverage"].is_active=False;d["coverage"].is_qualified=False;d["coverage"].save()
    with pytest.raises((ReleaseRefused,PermissionDenied)): release(d,attendance,**params)
    assert DaycareRelease.objects.count()==0
    assert AuditLog.objects.filter(action="diadem.daycare.release").count()==0

def test_foreign_tenant_staff_denied():
    d=setup(); attendance=check(d)
    foreign=School.objects.create(name="Other fictional center")
    stranger=UserAccount.objects.create_user(username="foreign_care_release",password="test",school=foreign)
    with pytest.raises(PermissionDenied): release(d,attendance,actor_id=stranger.id)
    assert DaycareRelease.objects.count()==0

def test_request_key_replay_denied():
    d=setup(); attendance=check(d); key=uuid4()
    release(d,attendance,request_key=key)
    with pytest.raises(ReleaseRefused) as error:release(d,attendance,request_key=key)
    assert error.value.code=="request_already_consumed"

def test_no_release_without_attendance():
    d=setup()
    with pytest.raises(ReleaseRefused):
        release_child(school_id=d["school"].id,actor_id=d["actor"].id,site_id=d["site"].id,
            room_id=d["room"].id,attendance_id=uuid4(),guardian_authority_id=d["authority"].id,
            request_key=uuid4(),identity_verified=True,identity_method="GOVERNMENT_PHOTO_ID")

def test_released_child_frees_room_but_no_same_day_reentry():
    from aftercare.models import DaycareChild,DaycareGuardianAuthority,DaycareEnrollment
    d=setup();d["room"].licensed_capacity=1;d["room"].save()
    first=check(d)
    second=DaycareChild.objects.create(school=d["school"],site=d["site"],household=d["family"],
        first_name="Second",last_name="Child",date_of_birth=d["child"].date_of_birth,is_active=True)
    DaycareGuardianAuthority.objects.create(school=d["school"],child=second,guardian=d["guardian"],
        is_active=True,can_pickup=True,custody_status="CLEAR",verified_by=d["director"],
        verified_at=timezone.now()-timedelta(minutes=5))
    DaycareEnrollment.objects.create(school=d["school"],site=d["site"],room=d["room"],
        child=second,program=d["program"],status="ACTIVE",readiness="READY",
        start_date=timezone.now().date()-timedelta(days=5),weekdays=list(range(7)))
    with pytest.raises(CheckinRefused):check(d,child_id=second.id)
    release(d,first)
    assert check(d,child_id=second.id).child_id==second.id
    assert DaycareAttendance.objects.filter(room=d["room"],custody_release__isnull=True).count()==1
    with pytest.raises(CheckinRefused) as error:check(d)
    assert error.value.code=="repeat_same_day_requires_review"

def test_suspended_tenant_must_still_permit_guarded_exit():
    from tenants.models import TenantProfile
    d=setup()
    attendance=check(d)
    tenant=TenantProfile.objects.get(school=d["school"])
    tenant.status="suspended"
    tenant.save(update_fields=["status"])
    d["entitlement"].enabled=False
    d["entitlement"].save(update_fields=["enabled"])
    exit_record=release(d,attendance)
    assert exit_record.attendance_id==attendance.id
    with pytest.raises(PermissionDenied):
        check(d)

def test_archived_child_still_has_guarded_release():
    d=setup()
    attendance=check(d)
    d["child"].is_active=False
    d["child"].save()
    assert release(d,attendance).attendance_id==attendance.id
