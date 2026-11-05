"""Portable synthetic policy tests; no Django or production identities required."""
from datetime import date, datetime, timedelta, timezone
from dataclasses import replace
from uuid import UUID
import pytest
from aftercare.daycare_policy import (
    CareEnrollment, Child, GuardianGrant, RoomOccupancy, RoomPolicy,
    StaffGrant, checkin_decision, guardian_read_decision,
)
SCHOOL=UUID("10000000-0000-0000-0000-000000000001")
OTHER_SCHOOL=UUID("10000000-0000-0000-0000-000000000002")
SITE=UUID("20000000-0000-0000-0000-000000000001")
OTHER_SITE=UUID("20000000-0000-0000-0000-000000000002")
CHILD_ID=UUID("30000000-0000-0000-0000-000000000001")
OTHER_CHILD=UUID("30000000-0000-0000-0000-000000000002")
HOUSEHOLD=UUID("40000000-0000-0000-0000-000000000001")
OTHER_HOUSEHOLD=UUID("40000000-0000-0000-0000-000000000002")
GUARDIAN=UUID("50000000-0000-0000-0000-000000000001")
OTHER_GUARDIAN=UUID("50000000-0000-0000-0000-000000000002")
DAY=date(2026,11,2)
NOW=datetime(2026,11,2,12,tzinfo=timezone.utc)

def eligible():
    return dict(school_id=SCHOOL,site_id=SITE,program_code="DAYCARE",local_date=DAY,
        child=Child(CHILD_ID,SCHOOL,HOUSEHOLD,SITE,True),
        enrollment=CareEnrollment(SCHOOL,SITE,CHILD_ID,"DAYCARE","ACTIVE","READY",DAY,None,(0,1,2,3,4)),
        staff=StaffGrant(SCHOOL,SITE,True,True),
        room=RoomPolicy(SCHOOL,SITE,True,12,4),
        occupancy=RoomOccupancy(3,1,False))

def guardian():
    return dict(school_id=SCHOOL,guardian_id=GUARDIAN,authenticated=True,
        child=eligible()["child"],
        grant=GuardianGrant(SCHOOL,HOUSEHOLD,CHILD_ID,GUARDIAN,True,True,True,"CLEAR"),
        at=NOW)

def check_denial(code, **changed):
    p=eligible();p.update(changed)
    d=checkin_decision(**p)
    assert not d.allowed and d.code == code

def guardian_denial(code, **changed):
    p=guardian();p.update(changed)
    d=guardian_read_decision(**p)
    assert not d.allowed and d.code == code

def test_no_k12_link_required():
    assert eligible()["child"].linked_student_id is None
    assert checkin_decision(**eligible()).allowed
    assert guardian_read_decision(**guardian()).allowed

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("site_id",OTHER_SITE,"scope_mismatch"),
    ("school_id","bad","invalid_identity"),
    ("site_id",UUID(int=0),"invalid_identity"),
    ("program_code","","invalid_program"),
    ("program_code","AFTER_CARE","program_mismatch"),
    ("local_date",datetime(2026,11,2,tzinfo=timezone.utc),"invalid_date"),
    ("local_date",DAY+timedelta(days=6),"not_scheduled"),
    ("local_date",DAY-timedelta(days=7),"outside_enrollment_dates"),
])
def test_checkin_context(field,value,code):
    check_denial(code,**{field:value})

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("site_id",OTHER_SITE,"scope_mismatch"),
    ("id",OTHER_CHILD,"scope_mismatch"),
    ("active",False,"authority_inactive"),
    ("active",None,"authority_inactive"),
])
def test_child_scope(field,value,code):
    p=eligible()
    check_denial(code,child=replace(p["child"],**{field:value}))

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("site_id",OTHER_SITE,"scope_mismatch"),
    ("active",False,"authority_inactive"),
    ("may_check_in",False,"authority_inactive"),
    ("may_check_in",None,"authority_inactive"),
])
def test_staff_scope(field,value,code):
    p=eligible()
    check_denial(code,staff=replace(p["staff"],**{field:value}))

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("site_id",OTHER_SITE,"scope_mismatch"),
    ("child_id",OTHER_CHILD,"scope_mismatch"),
    ("status","WAITLISTED","enrollment_not_ready"),
    ("status","CANCELLED","enrollment_not_ready"),
    ("status","EXPIRED","enrollment_not_ready"),
    ("readiness","BLOCKED","enrollment_not_ready"),
    ("readiness","INCOMPLETE","enrollment_not_ready"),
    ("program_code","PRESCHOOL","program_mismatch"),
    ("start_date",DAY+timedelta(days=1),"outside_enrollment_dates"),
    ("end_date",DAY-timedelta(days=1),"outside_enrollment_dates"),
    ("weekdays",(1,),"not_scheduled"),
    ("weekdays",(),"not_scheduled"),
    ("weekdays",(True,),"not_scheduled"),
    ("weekdays",(7,),"not_scheduled"),
])
def test_enrollment_scope(field,value,code):
    p=eligible()
    check_denial(code,enrollment=replace(p["enrollment"],**{field:value}))

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("site_id",OTHER_SITE,"scope_mismatch"),
    ("active",False,"authority_inactive"),
    ("licensed_capacity",None,"room_policy_missing"),
    ("max_children_per_staff",None,"room_policy_missing"),
    ("licensed_capacity",0,"room_policy_invalid"),
    ("max_children_per_staff",0,"room_policy_invalid"),
    ("licensed_capacity",True,"room_policy_missing"),
    ("licensed_capacity",3,"capacity_exceeded"),
    ("max_children_per_staff",3,"ratio_exceeded"),
])
def test_room_constraints(field,value,code):
    p=eligible()
    check_denial(code,room=replace(p["room"],**{field:value}))

@pytest.mark.parametrize("field,value,code",[
    ("children_present",-1,"room_policy_invalid"),
    ("children_present",4,"ratio_exceeded"),
    ("qualified_staff_present",0,"room_policy_invalid"),
    ("qualified_staff_present",None,"room_policy_missing"),
    ("qualified_staff_present",True,"room_policy_missing"),
    ("child_already_present",None,"occupancy_unknown"),
    ("child_already_present",True,"already_checked_in"),
])
def test_room_occupancy(field,value,code):
    p=eligible()
    check_denial(code,occupancy=replace(p["occupancy"],**{field:value}))

def test_room_boundaries():
    p=eligible()
    p["occupancy"]=RoomOccupancy(7,2,False)
    assert checkin_decision(**p).allowed
    p["occupancy"]=RoomOccupancy(11,3,False)
    assert checkin_decision(**p).allowed
    p["occupancy"]=RoomOccupancy(12,4,False)
    check_denial("capacity_exceeded",**p)

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("guardian_id",OTHER_GUARDIAN,"scope_mismatch"),
    ("authenticated",False,"authentication_required"),
    ("authenticated",None,"authentication_required"),
    ("at",datetime(2026,11,2,12),"invalid_time"),
])
def test_guardian_context(field,value,code):
    guardian_denial(code,**{field:value})

@pytest.mark.parametrize("field,value,code",[
    ("school_id",OTHER_SCHOOL,"scope_mismatch"),
    ("child_id",OTHER_CHILD,"scope_mismatch"),
    ("household_id",OTHER_HOUSEHOLD,"scope_mismatch"),
    ("guardian_id",OTHER_GUARDIAN,"scope_mismatch"),
    ("active",False,"authority_inactive"),
    ("verified",False,"authority_inactive"),
    ("can_view",False,"authority_inactive"),
    ("custody_status","RESTRICTED","custody_review_required"),
    ("custody_status","UNKNOWN","custody_review_required"),
    ("custody_status","","custody_review_required"),
    ("effective_from",NOW+timedelta(hours=1),"authority_expired"),
    ("effective_until",NOW,"authority_expired"),
    ("effective_until",datetime(2026,11,2,12),"invalid_authority_window"),
])
def test_guardian_grant(field,value,code):
    p=guardian()
    guardian_denial(code,grant=replace(p["grant"],**{field:value}))

def test_grant_window():
    p=guardian()
    p["grant"]=replace(p["grant"],effective_from=NOW-timedelta(days=1),effective_until=NOW+timedelta(days=1))
    assert guardian_read_decision(**p).allowed
    p["at"]=NOW+timedelta(days=1)
    assert not guardian_read_decision(**p).allowed

def test_program_isolation():
    p=eligible();p["program_code"]="PRESCHOOL"
    check_denial("program_mismatch",**p)
    p["enrollment"]=replace(p["enrollment"],program_code="PRESCHOOL")
    assert checkin_decision(**p).allowed
