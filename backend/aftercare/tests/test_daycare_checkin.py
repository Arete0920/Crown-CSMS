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
from core.models import School, UserAccount, UserRole, CrownPermission, RolePermission
from households.models import Household, Guardian
from subscriptions.models import Plan, Feature, TenantSubscription, EntitlementOverride
from tenants.models import TenantProfile
pytestmark=pytest.mark.django_db

def setup():
    school=School.objects.create(name="Synthetic childcare tenant",timezone="UTC")
    actor=UserAccount.objects.create_user(username="care_staff_synthetic",email="care_staff@synthetic.invalid",password="test",school=school)
    director=UserAccount.objects.create_user(username="care_director_synthetic",email="care_director@synthetic.invalid",password="test",school=school)
    UserRole.objects.create(school=school,user=actor,role_code="DAYCARE_STAFF")
    # TransactionTestCase flushes migration-seeded reference rows. Reconstruct
    # only this synthetic staff actor's explicit grants for isolated DB tests.
    for code in ("diadem.daycare.checkin","diadem.daycare.release"):
        permission, _ = CrownPermission.objects.get_or_create(
            code=code,defaults={"description":"Synthetic childcare test authorization"})
        RolePermission.objects.get_or_create(role_code="DAYCARE_STAFF",permission=permission)
    plan=Plan.objects.create(code="care_synthetic",name="Care synthetic")
    TenantSubscription.objects.create(school_id=school.pk,plan=plan)
    TenantProfile.objects.create(school=school,slug="diadem-synthetic-tenant",status="active")
    feature, _ = Feature.objects.get_or_create(
        key="diadem.daycare",
        defaults={"name":"Diadem Daycare and Preschool",
                  "description":"Synthetic default-off entitlement"})
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

@pytest.mark.parametrize("status",["pending","provisioning","suspended","offboarded"])
def test_non_active_tenant_blocks_checkin_without_audit(status):
    d=setup()
    tenant=TenantProfile.objects.get(school=d["school"])
    tenant.status=status
    tenant.save(update_fields=["status"])
    with pytest.raises(PermissionDenied):
        check(d)
    assert not DaycareAttendance.objects.exists()
    assert not AuditLog.objects.filter(action="diadem.daycare.checkin").exists()

def test_missing_tenant_profile_blocks_checkin():
    d=setup()
    TenantProfile.objects.filter(school=d["school"]).delete()
    with pytest.raises(PermissionDenied):
        check(d)
    assert not DaycareAttendance.objects.exists()

def test_overlapping_staff_room_assignment_rejected():
    from aftercare.models import DaycareRoomStaffCoverage, DaycareRoom
    from django.core.exceptions import ValidationError
    d=setup()
    other=DaycareRoom.objects.create(
        school=d["school"],site=d["site"],code="second-room",name="Second Room",
        licensed_capacity=4,max_children_per_staff=4,policy_source="Synthetic approved policy",
        policy_verified_by=d["director"],policy_verified_at=timezone.now()-timedelta(minutes=5),
        is_active=True,
    )
    now=timezone.now()
    with pytest.raises(ValidationError,match="overlapping"):
        DaycareRoomStaffCoverage.objects.create(
            school=d["school"],site=d["site"],room=other,staff=d["actor"],
            starts_at=now-timedelta(minutes=20),ends_at=now+timedelta(minutes=20),
            is_qualified=True,qualification_evidence="Synthetic qualification",
            verified_by=d["director"],verified_at=now-timedelta(minutes=5),is_active=True,
        )
    assert DaycareRoomStaffCoverage.objects.filter(staff=d["actor"]).count()==1

def test_adjacent_staff_room_assignment_allowed():
    from aftercare.models import DaycareRoomStaffCoverage, DaycareRoom
    d=setup()
    other=DaycareRoom.objects.create(
        school=d["school"],site=d["site"],code="later-room",name="Later Room",
        licensed_capacity=4,max_children_per_staff=4,policy_source="Synthetic approved policy",
        policy_verified_by=d["director"],policy_verified_at=timezone.now()-timedelta(minutes=5),
        is_active=True,
    )
    later=DaycareRoomStaffCoverage.objects.create(
        school=d["school"],site=d["site"],room=other,staff=d["actor"],
        starts_at=d["coverage"].ends_at,ends_at=d["coverage"].ends_at+timedelta(hours=1),
        is_qualified=True,qualification_evidence="Synthetic qualification",
        verified_by=d["director"],verified_at=timezone.now()-timedelta(minutes=5),is_active=True,
    )
    assert later.pk

def test_existing_shift_cannot_be_reassigned_to_other_staff_or_room():
    from core.models import UserAccount
    from django.core.exceptions import ValidationError
    d=setup()
    other=UserAccount.objects.create_user(
        username="another_daycare_staff",password="synthetic",school=d["school"])
    coverage=d["coverage"]
    coverage.staff=other
    with pytest.raises(ValidationError,match="identity is immutable"):
        coverage.save()
    coverage.refresh_from_db()
    assert coverage.staff_id==d["actor"].id
    another_room=DaycareRoom.objects.create(
        school=d["school"],site=d["site"],code="extra-room",name="Extra Room",
        licensed_capacity=4,max_children_per_staff=4,policy_source="Synthetic approved policy",
        policy_verified_by=d["director"],policy_verified_at=timezone.now()-timedelta(minutes=5),
        is_active=True)
    coverage.room=another_room
    with pytest.raises(ValidationError,match="identity is immutable"):
        coverage.save()
    coverage.refresh_from_db()
    assert coverage.room_id==d["room"].id

def test_revoking_staff_coverage_keeps_staff_identity():
    d=setup()
    coverage=d["coverage"]
    coverage.is_active=False
    coverage.save()
    coverage.refresh_from_db()
    assert coverage.staff_id==d["actor"].id
    assert coverage.is_active is False
    with pytest.raises(CheckinRefused):
        check(d)

def test_guardian_revocation_before_checkin_denies_entry():
    d=setup()
    d["authority"].is_active=False
    d["authority"].save()
    with pytest.raises(CheckinRefused) as error:
        check(d)
    assert error.value.code=="verified_pickup_authority_required"
    assert not DaycareAttendance.objects.exists()
    assert not AuditLog.objects.filter(action="diadem.daycare.checkin").exists()

def test_unverified_guardian_cannot_be_the_only_pickup_clearance():
    d=setup()
    d["authority"].is_active=False
    d["authority"].verified_by=None
    d["authority"].verified_at=None
    d["authority"].save()
    with pytest.raises(CheckinRefused) as error:
        check(d)
    assert error.value.code=="verified_pickup_authority_required"
    assert not DaycareAttendance.objects.exists()


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_arrivals_cannot_exceed_single_place():
    """Two real DB connections race for one room place; exactly one admission."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections, connections
    d=setup()
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent row-lock proof requires PostgreSQL.")
    d["room"].licensed_capacity=1
    d["room"].save()
    second=DaycareChild.objects.create(
        school=d["school"],site=d["site"],household=d["family"],
        first_name="Other",last_name="Synthetic",date_of_birth=d["child"].date_of_birth,
        is_active=True)
    DaycareGuardianAuthority.objects.create(
        school=d["school"],child=second,guardian=d["guardian"],is_active=True,
        can_pickup=True,custody_status="CLEAR",verified_by=d["director"],
        verified_at=timezone.now()-timedelta(minutes=5))
    DaycareEnrollment.objects.create(
        school=d["school"],site=d["site"],room=d["room"],child=second,
        program=d["program"],status="ACTIVE",readiness="READY",
        start_date=timezone.localdate()-timedelta(days=5),weekdays=list(range(7)))
    gate=Barrier(2)
    def attempt(child_id):
        close_old_connections()
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                backend_pid=cur.fetchone()[0]
            gate.wait(timeout=20)
            try:
                check(d,child_id=child_id)
                return backend_pid,"admitted"
            except CheckinRefused as error:
                return backend_pid,error.code
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        left=pool.submit(attempt,d["child"].id)
        right=pool.submit(attempt,second.id)
        outcomes=[left.result(timeout=40),right.result(timeout=40)]
    assert len({pid for pid,_ in outcomes})==2, outcomes
    assert sorted(result for _,result in outcomes)==["admitted","capacity_exceeded"],outcomes
    assert DaycareAttendance.objects.filter(school=d["school"],custody_release__isnull=True).count()==1
    assert AuditLog.objects.filter(action="diadem.daycare.checkin").count()==1


@pytest.mark.django_db(transaction=True)
def test_postgresql_concurrent_staff_assignments_cannot_overlap():
    """Two inserts for a shared employee must serialize even across different rooms."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import connection, close_old_connections, connections
    d=setup()
    if connection.vendor != "postgresql":
        pytest.skip("Concurrent row-lock proof requires PostgreSQL.")
    d["coverage"].is_active=False
    d["coverage"].save()
    rooms=[]
    for code in ("race-room-a","race-room-b"):
        rooms.append(DaycareRoom.objects.create(
            school=d["school"],site=d["site"],code=code,name=code,
            licensed_capacity=4,max_children_per_staff=4,
            policy_source="Synthetic reviewed room approval",
            policy_verified_by=d["director"],
            policy_verified_at=timezone.now()-timedelta(minutes=5),is_active=True))
    at=timezone.now()
    gate=Barrier(2)
    def attempt(room_id):
        close_old_connections()
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                pid=cur.fetchone()[0]
            gate.wait(timeout=20)
            try:
                DaycareRoomStaffCoverage.objects.create(
                    school=d["school"],site=d["site"],room_id=room_id,staff=d["actor"],
                    starts_at=at-timedelta(minutes=10),ends_at=at+timedelta(hours=1),
                    is_qualified=True,qualification_evidence="Synthetic attested credential",
                    verified_by=d["director"],
                    verified_at=at-timedelta(minutes=5),is_active=True)
                return pid,"assigned"
            except ValidationError as error:
                return pid,"overlapping" if "overlapping" in str(error) else str(error)
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(attempt,room.id) for room in rooms]
        outcomes=[future.result(timeout=40) for future in futures]
    assert len({pid for pid,_ in outcomes})==2,outcomes
    assert sorted(result for _,result in outcomes)==["assigned","overlapping"],outcomes
    assert DaycareRoomStaffCoverage.objects.filter(
        school=d["school"],staff=d["actor"],is_active=True).count()==1
