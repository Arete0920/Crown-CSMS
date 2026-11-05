"""Synthetic database tests for standalone Diadem foundation; no K-12 enrollment required."""
from datetime import date
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from aftercare.models import (DaycareSite,DaycareRoom,DaycareChild,
    DaycareGuardianAuthority,DaycareProgram,DaycareEnrollment)
from core.models import School,UserAccount
from households.models import Household,Guardian,Student

pytestmark=pytest.mark.django_db

def fixture():
    a=School.objects.create(name="Fictional Diadem Alpha")
    b=School.objects.create(name="Fictional Diadem Beta")
    aa=UserAccount.objects.create_user(username="daycare_alpha",password="synthetic",school=a)
    bb=UserAccount.objects.create_user(username="daycare_beta",password="synthetic",school=b)
    ah=Household.objects.create(school_id=a.id,name="Alpha family")
    bh=Household.objects.create(school_id=b.id,name="Beta family")
    ag=Guardian.objects.create(school_id=a.id,household=ah,first_name="Alpha",last_name="Parent")
    bg=Guardian.objects.create(school_id=b.id,household=bh,first_name="Beta",last_name="Parent")
    sa=DaycareSite.objects.create(school=a,code="north",name="North Center",is_active=True)
    sb=DaycareSite.objects.create(school=b,code="north",name="North Center",is_active=True)
    room=DaycareRoom.objects.create(school=a,site=sa,code="sun",name="Sun Room",
        licensed_capacity=12,max_children_per_staff=4,policy_source="Synthetic reviewed policy",
        policy_verified_by=aa,policy_verified_at=timezone.now(),is_active=True)
    program=DaycareProgram.objects.create(school=a,site=sa,code="DAYCARE",name="Daycare",is_active=True)
    child=DaycareChild.objects.create(school=a,site=sa,household=ah,
        first_name="Tiny",last_name="Learner",date_of_birth=date(2022,1,15),is_active=True)
    return locals()

def test_standalone_child_needs_no_k12_student_and_defaults_are_closed():
    d=fixture()
    assert d["child"].linked_student_id is None
    enrollment=DaycareEnrollment.objects.create(school=d["a"],site=d["sa"],child=d["child"],
        program=d["program"],start_date=date(2026,11,2),weekdays=[0,1,2,3,4])
    authority=DaycareGuardianAuthority.objects.create(school=d["a"],child=d["child"],guardian=d["ag"])
    assert (enrollment.status,enrollment.readiness)==("WAITLISTED","INCOMPLETE")
    assert not authority.is_active and not authority.verified and not authority.can_pickup

@pytest.mark.parametrize("foreign_ref",["sb","bh"])
def test_foreign_site_or_household_is_blocked(foreign_ref):
    d=fixture()
    kwargs=dict(school=d["a"],site=d["sa"],household=d["ah"],
        first_name="Wrong",last_name="Scope",date_of_birth=date(2023,1,1))
    kwargs["site" if foreign_ref=="sb" else "household"]=d[foreign_ref]
    with pytest.raises(ValidationError):
        DaycareChild.objects.create(**kwargs)

def test_guardian_grant_denies_foreign_household_and_unverified_authority():
    d=fixture()
    with pytest.raises(ValidationError):
        DaycareGuardianAuthority.objects.create(school=d["a"],child=d["child"],guardian=d["bg"])
    base=dict(school=d["a"],child=d["child"],guardian=d["ag"],
              is_active=True,can_view=True,custody_status="CLEAR")
    with pytest.raises(ValidationError):
        DaycareGuardianAuthority.objects.create(**base)
    with pytest.raises(ValidationError):
        DaycareGuardianAuthority.objects.create(**base,verified_by=d["bb"],verified_at=timezone.now())
    with pytest.raises(ValidationError):
        DaycareGuardianAuthority.objects.create(**{**base,"custody_status":"RESTRICTED"},
                                                verified_by=d["aa"],verified_at=timezone.now())
    valid=DaycareGuardianAuthority.objects.create(**base,verified_by=d["aa"],verified_at=timezone.now())
    assert valid.verified and valid.is_active

@pytest.mark.parametrize("overrides",[
    {"licensed_capacity":None},{"max_children_per_staff":None},{"licensed_capacity":0},
    {"policy_source":""},{"policy_verified_at":None},
])
def test_room_must_have_explicit_policy_to_activate(overrides):
    d=fixture()
    args=dict(school=d["a"],site=d["sa"],code="new",name="Room",
        licensed_capacity=12,max_children_per_staff=4,policy_source="Verified synthetic",
        policy_verified_by=d["aa"],policy_verified_at=timezone.now(),is_active=True)
    args.update(overrides)
    with pytest.raises(ValidationError):
        DaycareRoom.objects.create(**args)

@pytest.mark.parametrize("overrides",[
    {"site":"sb"},{"room":None},{"weekdays":[]},{"weekdays":[0,0]},
    {"weekdays":[True]},{"weekdays":[7]},{"end_date":date(2026,11,1)},
])
def test_enrollment_requires_matching_site_dates_and_explicit_room(overrides):
    d=fixture()
    args=dict(school=d["a"],site=d["sa"],child=d["child"],program=d["program"],
        room=d["room"],status="ACTIVE",readiness="READY",
        start_date=date(2026,11,2),weekdays=[0,1,2,3,4])
    for key,value in overrides.items():
        args[key]=d[value] if value=="sb" else value
    with pytest.raises(ValidationError):
        DaycareEnrollment.objects.create(**args)

def test_valid_ready_enrollment_is_saved():
    d=fixture()
    e=DaycareEnrollment.objects.create(school=d["a"],site=d["sa"],child=d["child"],
        program=d["program"],room=d["room"],status="ACTIVE",readiness="READY",
        start_date=date(2026,11,2),weekdays=[0,1,2,3,4])
    assert e.pk

def test_k12_promotion_reference_cannot_cross_tenants():
    d=fixture()
    foreign=Student.objects.create(school_id=d["b"].pk,household=d["bh"],
        first_name="Other",last_name="Student")
    d["child"].linked_student=foreign
    with pytest.raises(ValidationError):
        d["child"].save()

def test_bulk_and_hard_delete_are_blocked():
    d=fixture()
    with pytest.raises(ValidationError): d["child"].delete()
    with pytest.raises(ValidationError): DaycareChild.objects.filter(school=d["a"]).delete()
    with pytest.raises(ValidationError): DaycareChild.objects.filter(school=d["a"]).update(is_active=False)
    with pytest.raises(ValidationError): DaycareChild.objects.bulk_create([d["child"]])
    with pytest.raises(ValidationError): DaycareChild.objects.bulk_update([d["child"]],["is_active"])
