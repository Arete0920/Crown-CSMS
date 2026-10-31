"""Synthetic Django check-in contract; requires real DB CI and PostgreSQL lock proof."""
from datetime import timedelta
from uuid import uuid4
import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied
from aftercare.daycare_checkin import checkin_child, CheckinRefused
from aftercare.models import (DaycareSite,DaycareRoom,DaycareChild,DaycareProgram,
    DaycareEnrollment,DaycareGuardianAuthority,DaycareAttendance,DaycareRoomStaffCoverage)
from audit.models import AuditLog
from core.models import School, UserAccount, UserRole
from households.models import Household, Guardian
from subscriptions.models import Plan, Feature, TenantSubscription, EntitlementOverride
pytestmark=pytest.mark.django_db

def setup():
    school=School.objects.create(name="Synthetic childcare tenant",timezone="UTC")
    actor=UserAccount.objects.create_user(username="care_staff_synthetic",password="test",school=school)
    director=UserAccount.objects.create_user(username="care_director_synthetic",password="test",school=school)
    UserRole.objects.create(school=school,user=actor,role_code="DAYCARE_STAFF")
    plan=Plan.objects.create(code="care_synthetic",name="Care synthetic")
    TenantSubscription.objects.create(school_id=school.pk,plan=plan)
    feature=Feature.objects.get(key="diadem.daycare")
    entitlement=EntitlementOverride.objects.create(school_id=school.pk,feature=feature,enabled=True)
    site=DaycareSite.objects.create(school=school,code="center",name="Synthetic Center",is_active=True)
    now=timezone.now()
    room=DaycareRoom.objects.create(school=school,site=site,code="toddler",name="Toddler",
        licensed_capacity=4,max_children_per_staff=4,policy_source="Synthetic approved policy",
        policy_verified_by=director,policy_verified_at=now-timedelta(minutes=5),is_active=True)
    family=Household.objects.create(school_id=school.id,name="Synthetic Household")
    guardian=Guardian.objects.create(school_id=school.id,household=family,
        first_name="Synthetic",last_name="Guardian")
    program=DaycareProgram.objects.create(school=school,site=site,code="DAYCARE",name="Daycare",is_active=True)
    child=DaycareChild.objects.create(school=school,site=site,household=family,
        first_name="Synthetic",last_name="Child",date_of_birth=now.date()-timedelta(days=900),is_active=True)
    authority=DaycareGuardianAuthority.objects.create(school=school,child=child,guardian=guardian,
        is_active=True,can_pickup=True,custody_status="CLEAR",verified_by=director,
        verified_at=now-timedelta(minutes=5))
    enrollment=DaycareEnrollment.objects.create(school=school,site=site,room=room,
        child=child,program=program,status="ACTIVE",readiness="READY",
        start_date=now.date()-timedelta(days=5),weekdays=list(range(7)))
    coverage=DaycareRoomStaffCoverage.objects.create(school=school,site=site,room=room,
        staff=actor,starts_at=now-timedelta(hours=1),ends_at=now+timedelta(hours=2),
        is_qualified=True,qualification_evidence="Synthetic qualification",verified_by=director,
        verified_at=now-timedelta(minutes=5),is_active=True)
    return locals()

def check(d,**changes):
    values=dict(school_id=d["school"].id,actor_id=d["actor"].id,site_id=d["site"].id,
        room_id=d["room"].id,child_id=d["child"].id,program_code="DAYCARE",request_key=uuid4())
    values.update(changes)
    return checkin_child(**values)

def test_checkin_audits_once_and_denies_repeat():
    d=setup()
    row=check(d)
    assert row.child_id==d["child"].id
    assert AuditLog.objects.filter(action="diadem.daycare.checkin",object_id=str(row.id)).count()==1
    with pytest.raises(ValidationError): row.save()
    with pytest.raises(CheckinRefused) as e: check(d)
    assert e.value.code=="already_checked_in"
    assert DaycareAttendance.objects.count()==1

@pytest.mark.parametrize("reason",["entitlement","custody","staffing"])
def test_no_side_effect_on_missing_safety_gate(reason):
    d=setup()
    if reason=="entitlement":
        d["entitlement"].enabled=False
        d["entitlement"].save(update_fields=["enabled"])
    elif reason=="custody":
        d["authority"].is_active=False
        d["authority"].save()
    else:
        d["coverage"].is_active=False
        d["coverage"].save()
    with pytest.raises((PermissionDenied,CheckinRefused)): check(d)
    assert DaycareAttendance.objects.count()==0
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count()==0

def test_foreign_tenant_staff_denied():
    d=setup()
    foreign=School.objects.create(name="Synthetic foreign tenant")
    user=UserAccount.objects.create_user(username="foreign_care_staff",password="test",school=foreign)
    with pytest.raises(PermissionDenied): check(d,actor_id=user.id)
    assert DaycareAttendance.objects.count()==0

def test_request_key_uniqueness():
    d=setup()
    key=uuid4()
    check(d,request_key=key)
    with pytest.raises(CheckinRefused): check(d,request_key=key)
    assert DaycareAttendance.objects.count()==1
