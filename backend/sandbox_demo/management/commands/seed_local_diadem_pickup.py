"""Synthetic Heritage Diadem pickup evidence for the loopback-only local demo.

This is NOT a customer seeder, daycare approval, production fixture, or safety
certification. No real children, school provisioning, payments, or network writes.
Creates a new one-use fictional scenario; never resets or deletes custody rows.
"""
from __future__ import annotations

import json
import os
import secrets
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken

from audit.models import AuditLog
from aftercare.daycare_checkin import checkin_child
from aftercare.models import (
    DaycareChild, DaycareEnrollment, DaycareGuardianAuthority, DaycareProgram,
    DaycareRelease, DaycareRoom, DaycareRoomStaffCoverage, DaycareSite,
)
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from households.models import Guardian, Household
from subscriptions.models import EntitlementOverride, Feature, Plan, TenantSubscription
from tenants.models import TenantProfile
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.management.commands.five_module_demo_preflight import (
    LOCAL_DB, _require_isolated_local_database,
)

MANIFEST = LOCAL_DB.parent / "diadem-pickup-session.json"


def require_local_demo():
    _require_isolated_local_database()
    if os.environ.get("VITE_LOCAL_DEMO") != "1" or os.environ.get("DJANGO_ENV") != "local":
        raise CommandError("Diadem pickup evidence is restricted to the isolated local Heritage launcher.")


def local_token(user, school):
    token = AccessToken.for_user(user)
    token["school_id"] = str(school.pk)
    token.set_exp(lifetime=timedelta(minutes=30))
    return str(token)


@transaction.atomic
def build_scenario():
    spec = SANDBOX_SCHOOLS["heritage-core"]
    school = School.objects.filter(pk=UUID(spec.id), name=spec.name, is_active=True).first()
    if school is None:
        raise CommandError("Prepare the fictional Heritage demo school before Diadem pickup evidence.")

    profile, _ = TenantProfile.objects.get_or_create(
        school=school,
        defaults={"slug": "heritage-diadem-local-only", "status": "active", "payment_provider": "none"},
    )
    if profile.status != "active":
        raise CommandError("Demo tenant is inactive; do not silently override its lifecycle.")
    subscriptions = list(TenantSubscription.objects.filter(school_id=school.pk, ended_at__isnull=True))
    if len(subscriptions) > 1:
        raise CommandError("Ambiguous local demo subscription; do not create childcare enrollment.")
    if not subscriptions:
        plan, _ = Plan.objects.get_or_create(
            code="heritage_diadem_local", defaults={"name": "Fictional Heritage local daycare proof"}
        )
        if not plan.is_active:
            raise CommandError("Local demo plan is inactive.")
        TenantSubscription.objects.create(school_id=school.pk, plan=plan)
    elif not subscriptions[0].plan.is_active:
        raise CommandError("Existing demo subscription plan is inactive.")

    feature, _ = Feature.objects.get_or_create(
        key="diadem.daycare", defaults={"name": "Diadem Daycare", "description": "Local fictional proof"}
    )
    EntitlementOverride.objects.update_or_create(
        school_id=school.pk, feature=feature, defaults={"enabled": True}
    )
    for role, codes in (
        ("DAYCARE_STAFF", ("diadem.daycare.view", "diadem.daycare.checkin", "diadem.daycare.release")),
        ("DAYCARE_DIRECTOR", ("diadem.daycare.view", "diadem.daycare.release")),
    ):
        for code in codes:
            permission, _ = CrownPermission.objects.get_or_create(
                code=code, defaults={"description": "Canonical Diadem scoped operation"}
            )
            RolePermission.objects.get_or_create(role_code=role, permission=permission)

    scenario = secrets.token_hex(5)
    now = timezone.now()
    local_day = timezone.localtime(now, ZoneInfo(school.timezone)).date()

    def actor(label, role):
        username = "fictional-diadem-" + label + "-" + scenario + "@example.invalid"
        user = UserAccount.objects.create_user(
            username=username, email=username, password=None, school=school,
            first_name="Fictional", last_name=label.title(),
        )
        UserRole.objects.create(school=school, user=user, role_code=role)
        return user

    staff = actor("staff", "DAYCARE_STAFF")
    director = actor("director", "DAYCARE_DIRECTOR")
    observer = actor("observer", "PARENT")
    site = DaycareSite.objects.create(
        school=school, code="pickup-" + scenario, name="Fictional Diadem Pickup Center",
        is_active=True,
    )
    room = DaycareRoom.objects.create(
        school=school, site=site, code="care-room", name="Fictional Care Room",
        licensed_capacity=4, max_children_per_staff=4,
        policy_source="SYNTHETIC LOCAL TEST ONLY - not a licensing approval",
        policy_verified_by=director, policy_verified_at=now - timedelta(minutes=5),
        is_active=True,
    )
    program = DaycareProgram.objects.create(
        school=school, site=site, code="DAYCARE", name="Fictional Daycare", is_active=True,
    )
    household = Household.objects.create(
        school_id=school.pk, name="Fictional Diadem Household " + scenario,
    )
    guardian = Guardian.objects.create(
        school_id=school.pk, household=household,
        first_name="Fictional", last_name="Guardian",
    )
    DaycareRoomStaffCoverage.objects.create(
        school=school, site=site, room=room, staff=staff,
        starts_at=now - timedelta(hours=1), ends_at=now + timedelta(hours=2),
        is_qualified=True, qualification_evidence="FICTIONAL TEST EVIDENCE - no real staff credentials",
        verified_by=director, verified_at=now - timedelta(minutes=5), is_active=True,
    )

    cases = {}
    for case, surname in (
        ("approved", "Pickup"), ("revoked", "Revoked"), ("expired", "Expired")
    ):
        child = DaycareChild.objects.create(
            school=school, site=site, household=household,
            first_name="Fictional", last_name=surname,
            date_of_birth=local_day - timedelta(days=1000), is_active=True,
        )
        authority = DaycareGuardianAuthority.objects.create(
            school=school, child=child, guardian=guardian,
            is_active=True, can_pickup=True, custody_status="CLEAR",
            verified_by=director, verified_at=now - timedelta(minutes=5),
        )
        DaycareEnrollment.objects.create(
            school=school, site=site, room=room, child=child, program=program,
            status="ACTIVE", readiness="READY",
            start_date=local_day - timedelta(days=7), weekdays=list(range(7)),
        )
        attendance = checkin_child(
            school_id=school.pk, actor_id=staff.pk, site_id=site.pk, room_id=room.pk,
            child_id=child.pk, program_code="DAYCARE", request_key=uuid4(),
        )
        # Admit through the real service first, then create denied pickup cases.
        if case == "revoked":
            authority.is_active = False
            authority.save(update_fields=["is_active"])
        elif case == "expired":
            authority.effective_until = timezone.now() - timedelta(seconds=1)
            authority.save(update_fields=["effective_until"])
        cases[case] = {
            "attendance_id": str(attendance.pk),
            "authority_id": str(authority.pk),
            "child_name": child.first_name + " " + child.last_name,
        }

    return {
        "fictional_only": True,
        "scenario": scenario,
        "school_id": str(school.pk),
        "site_id": str(site.pk),
        "room_id": str(room.pk),
        "guardian_name": "Fictional Guardian",
        "cases": cases,
        "staff_access": local_token(staff, school),
        "unprivileged_access": local_token(observer, school),
        "source_sha": os.environ.get("BUILD_SHA", ""),
    }


def verify_scenario():
    if not MANIFEST.is_file():
        raise CommandError("No local Diadem pickup browser scenario manifest.")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("fictional_only") is not True:
        raise CommandError("Refusing unverified Diadem scenario manifest.")
    if data.get("school_id") != SANDBOX_SCHOOLS["heritage-core"].id:
        raise CommandError("Diadem scenario does not belong to the fictional Heritage tenant.")
    approved = data["cases"]["approved"]["attendance_id"]
    denied = [
        data["cases"]["revoked"]["attendance_id"],
        data["cases"]["expired"]["attendance_id"],
    ]
    releases = list(DaycareRelease.objects.filter(
        school_id=data["school_id"], attendance_id=approved
    ))
    if len(releases) != 1:
        raise CommandError("Expected exactly one persisted synthetic custody release.")
    event = releases[0]
    if (not event.identity_verified or event.actor.school_id != UUID(data["school_id"])
            or event.guardian_authority_id != UUID(data["cases"]["approved"]["authority_id"])
            or AuditLog.objects.filter(action="diadem.daycare.release", object_id=str(event.pk)).count() != 1):
        raise CommandError("Synthetic custody handoff audit or recipient binding is invalid.")
    if DaycareRelease.objects.filter(
        school_id=data["school_id"], attendance_id__in=denied
    ).exists():
        raise CommandError("A synthetic forbidden custody release was persisted.")
    return data["scenario"]


class Command(BaseCommand):
    help = "Seed or verify a one-use fictional Diadem pickup in isolated local Heritage SQLite."

    def add_arguments(self, parser):
        parser.add_argument(
            "--verify", action="store_true",
            help="Read back custody and audit evidence after authenticated browser execution.",
        )

    def handle(self, *args, **options):
        require_local_demo()
        if options["verify"]:
            scenario = verify_scenario()
            self.stdout.write(self.style.SUCCESS(
                "PASS fictional Diadem browser release persisted once; revoked and expired releases absent. Scenario " + scenario
            ))
            return
        data = build_scenario()
        MANIFEST.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        try:
            MANIFEST.chmod(0o600)
        except OSError:
            pass  # Windows local-only temporary evidence; never uploaded.
        self.stdout.write(self.style.SUCCESS(
            "Prepared fictional Diadem pickup scenario " + data["scenario"] + " at " + str(MANIFEST)
        ))
