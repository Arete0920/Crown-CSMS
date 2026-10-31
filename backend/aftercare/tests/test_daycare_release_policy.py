"""Pure custody decision tests: no Django/database dependencies."""
from dataclasses import replace
from datetime import date,datetime,timedelta,timezone
from uuid import UUID
import pytest
from aftercare.daycare_policy import Child
from aftercare.daycare_release_policy import (
    CheckedIn,ReleasingStaff,RecipientAuthority,release_decision)
S=UUID(int=1);T=UUID(int=2);SITE=UUID(int=3);ROOM=UUID(int=4)
CHILD=UUID(int=5);HOUSE=UUID(int=6);STAFF=UUID(int=7);GUARD=UUID(int=8)
NOW=datetime(2026,11,2,17,tzinfo=timezone.utc)
DAY=date(2026,11,2)
def baseline():
    return dict(school_id=S,site_id=SITE,actor_id=STAFF,guardian_id=GUARD,
        child=Child(CHILD,S,HOUSE,SITE,True),
        attendance=CheckedIn(S,SITE,ROOM,CHILD,DAY,NOW-timedelta(hours=2),False),
        staff=ReleasingStaff(S,SITE,ROOM,STAFF,True,True,True),
        authority=RecipientAuthority(S,HOUSE,CHILD,GUARD,True,True,True,"CLEAR",None,None),
        at=NOW,local_day=DAY,authenticated=True,identity_verified=True,
        identity_method="GOVERNMENT_PHOTO_ID")
def test_positive_decision():
    d=release_decision(**baseline());assert d.allowed and d.code=="authorized_release"
@pytest.mark.parametrize("field,value,reason",[
    ("authenticated",False,"authentication_required"),
    ("identity_verified",False,"identity_verification_required"),
    ("identity_method","SELF_ATTESTED","identity_verification_required"),
    ("local_day",date(2026,11,3),"overnight_release_requires_director_review"),
    ("actor_id",T,"scope_mismatch"),
    ("guardian_id",T,"scope_mismatch"),
    ("site_id",T,"scope_mismatch"),
    ("school_id",T,"scope_mismatch"),
])
def test_context_denial(field,value,reason):
    p=baseline();p[field]=value;d=release_decision(**p);assert not d.allowed and d.code==reason
@pytest.mark.parametrize("field,value,reason",[
    ("active",False,"staff_or_child_inactive"),
    ("qualified_on_duty",False,"staff_or_child_inactive"),
    ("may_release",False,"staff_or_child_inactive"),
    ("room_id",T,"scope_mismatch"),
])
def test_staff_denial(field,value,reason):
    p=baseline();p["staff"]=replace(p["staff"],**{field:value})
    d=release_decision(**p);assert not d.allowed and d.code==reason
@pytest.mark.parametrize("field,value,reason",[
    ("active",False,"recipient_not_authorized"),
    ("verified",False,"recipient_not_authorized"),
    ("can_pickup",False,"recipient_not_authorized"),
    ("custody_status","RESTRICTED","custody_review_required"),
    ("household_id",T,"scope_mismatch"),
    ("child_id",T,"scope_mismatch"),
    ("guardian_id",T,"scope_mismatch"),
    ("effective_from",NOW+timedelta(minutes=1),"authority_outside_window"),
    ("effective_until",NOW,"authority_outside_window"),
])
def test_recipient_denial(field,value,reason):
    p=baseline();p["authority"]=replace(p["authority"],**{field:value})
    d=release_decision(**p);assert not d.allowed and d.code==reason
@pytest.mark.parametrize("field,value,reason",[
    ("released",True,"already_released"),
    ("released",None,"attendance_state_unknown"),
    ("room_id",T,"scope_mismatch"),
    ("care_date",date(2026,11,1),"overnight_release_requires_director_review"),
    ("checked_in_at",NOW+timedelta(minutes=1),"release_before_checkin"),
])
def test_attendance_denial(field,value,reason):
    p=baseline();p["attendance"]=replace(p["attendance"],**{field:value})
    d=release_decision(**p);assert not d.allowed and d.code==reason
