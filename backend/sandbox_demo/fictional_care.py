"""Shared fictional care fixtures; neither customer custody nor licensing authority."""
from datetime import date, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from aftercare.daycare_models import (DaycareSite, DaycareRoom, DaycareChild,
    DaycareProgram, DaycareEnrollment, DaycareGuardianAuthority)
from aftercare.daycare_checkin_models import DaycareRoomStaffCoverage
from households.models import Household, Guardian
from subscriptions.models import Feature, Plan, PlanEntitlement, TenantSubscription, SchoolModule
from tenants.models import TenantProfile


def require_fictional_care_scope(school, workspace=None, *, custody=False):
    # Recheck authority even when these helpers are called directly. Caller
    # transactions keep the exact-school locks through the fixture commit.
    if workspace is None:
        from .universal_demo import require_local_presenter, _owned_school
        require_local_presenter()
        owned = _owned_school()
        if owned is None or owned.pk != school.pk:
            raise CommandError("Care fixtures require the owned local presenter school.")
        return "buyer-care"  # Existing service enforces this school-specific seven-day license.
    from .management.commands import provision_hosted_buyer_care_entitlements as authority
    if custody:
        from .management.commands import seed_hosted_buyer_daycare as runtime
    else:
        runtime = authority
    runtime._require_existing_dev_runtime(workspace.source_sha)
    checked = authority._checked_workspace(workspace.invite_id, workspace.source_sha)
    if checked.pk != workspace.pk or checked.school_id != school.pk:
        raise CommandError("Care fixtures require the exact authorized fictional workspace.")
    return "buyer-care"


@transaction.atomic
def seed_care_entitlements(school, *, workspace=None):
    prefix = require_fictional_care_scope(school, workspace)
    from .management.commands.provision_hosted_buyer_care_entitlements import _assert_empty, _CARE_KEYS
    _assert_empty(school)
    if Plan.objects.filter(code=f"{prefix}-{school.pk.hex}").exists():
        raise CommandError("Existing fictional plan requires separate review.")
    # A buyer-specific plan cannot extend entitlements for other schools.
    plan = Plan.objects.create(
        code=f"{prefix}-{school.pk.hex}",
        name="Fictional buyer childcare evaluation",
        description="Synthetic Azure DEV demonstration, no commercial billing.",
        is_active=True,
    )
    feature, _ = Feature.objects.get_or_create(
        key="diadem.daycare", defaults={"name": "Diadem Daycare"}
    )
    PlanEntitlement.objects.create(plan=plan, feature=feature, enabled=True)
    TenantProfile.objects.create(
        school=school, slug=f"{prefix}-{school.pk.hex}",
        plan_code="starter", status="active", payment_provider="none",
    )
    TenantSubscription.objects.create(
        school_id=school.pk, plan=plan, started_at=timezone.now(), is_trial=True,
    )
    expires_at = timezone.now() + timedelta(days=7)
    for key in _CARE_KEYS:
        SchoolModule.objects.create(
            school=school, module_key=key, status="active",
            expiry_date=expires_at,
            notes="Fictional invite-bound DEV proof only; not a license or policy attestation.",
        )


@transaction.atomic
def seed_daycare_records(school, director_and_staff, *, workspace=None):
    require_fictional_care_scope(school, workspace, custody=True)
    from .management.commands.seed_hosted_buyer_daycare import (
        _empty_synthetic_care, _HOUSEHOLD, _SOURCE, _QUALIFICATION,
    )
    from core.models import UserAccount, UserRole
    from .universal_identity import presenter_username
    from .buyer_workspace import buyer_username
    from aftercare.daycare_checkin import require_entitlement
    require_entitlement(school.pk)
    _empty_synthetic_care(school)
    for key, role in (("daycare_director", "DAYCARE_DIRECTOR"), ("daycare_staff", "DAYCARE_STAFF")):
        username = presenter_username(key) if workspace is None else buyer_username(school.pk, key)
        actor = director_and_staff.get(key)
        if actor is None or not UserAccount.objects.select_for_update().filter(
            pk=actor.pk, school=school, username=username, is_active=True,
            is_staff=False, is_superuser=False,
        ).exists() or not UserRole.objects.select_for_update().filter(
            school=school, user=actor, role_code=role,
        ).exists():
            raise CommandError("Exact-school fictional care principal and role required.")
    now = timezone.now()
    try:
        care_day = timezone.localtime(now, ZoneInfo(school.timezone)).date()
    except (TypeError, ValueError, ZoneInfoNotFoundError) as exc:
        raise CommandError("A valid fictional school timezone is required.") from exc
    director = director_and_staff["daycare_director"]
    staff = director_and_staff["daycare_staff"]
    site = DaycareSite.objects.create(
        school=school, code="fictional-daycare", name="Fictional Demo Daycare",
        operating_mode="STANDALONE", jurisdiction="US-DE", is_active=True,
    )
    room = DaycareRoom.objects.create(
        school=school, site=site, code="fictional-room",
        name="Fictional Demonstration Room", is_active=True,
        licensed_capacity=4, max_children_per_staff=4,
        policy_source=_SOURCE, policy_verified_by=director,
        policy_verified_at=now,
    )
    household = Household.objects.create(
        school_id=school.pk, name=_HOUSEHOLD, is_active=True,
    )
    guardian = Guardian.objects.create(
        school_id=school.pk, household=household,
        first_name="Fictional", last_name="Guardian", is_primary=True,
    )
    child = DaycareChild.objects.create(
        school=school, site=site, household=household,
        first_name="Fictional", last_name="Child",
        date_of_birth=date(2022, 1, 15), is_active=True,
    )
    program = DaycareProgram.objects.create(
        school=school, site=site, code="DAYCARE",
        name="Fictional Daycare Program", is_active=True,
    )
    DaycareEnrollment.objects.create(
        school=school, site=site, child=child, program=program,
        room=room, status="ACTIVE", readiness="READY",
        start_date=care_day - timedelta(days=1),
        end_date=care_day + timedelta(days=7),
        weekdays=list(range(7)),
    )
    DaycareGuardianAuthority.objects.create(
        school=school, child=child, guardian=guardian,
        is_active=True, can_view=True, can_pickup=True,
        custody_status="CLEAR",
        verified_by=director, verified_at=now,
        effective_from=now - timedelta(hours=1),
        effective_until=now + timedelta(days=7),
    )
    DaycareRoomStaffCoverage.objects.create(
        school=school, site=site, room=room, staff=staff,
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(hours=8),
        is_active=True, is_qualified=True,
        qualification_evidence=_QUALIFICATION,
        verified_by=director, verified_at=now,
    )
    return {"site_id": str(site.pk), "room_id": str(room.pk),
            "child_id": str(child.pk), "guardian_id": str(guardian.pk), "care_day": str(care_day)}
