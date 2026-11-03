"""Add strictly fictional Heritage module samples to a prepared LOCAL demo.

This fills only the Financial Aid, AM/PM Extended Care and Diadem sample-data
inventory. Camp and partner-SGO fixtures have separately maintained owners.
Sample childcare enrollment is deliberately BLOCKED: this seeder never
attests custody, approves room capacity/ratios, or grants staff permissions.
"""
from __future__ import annotations

import os
import uuid
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.management.base import CommandError
from django.db import transaction

from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.management.commands.five_module_demo_preflight import (
    _require_isolated_local_database,
)

# Never accept a caller-redefined CROWN_DEMO_SCHOOL_ID as authority to seed.
HERITAGE_ID = uuid.UUID("19801b59-8c05-4c84-9312-5d792e4e839d")
NAMESPACE = uuid.UUID("6f4445a7-1dcc-42dd-87ac-3cfe5fa4e9e1")
SAMPLE_START = date(2026, 8, 1)


def fixed_id(label: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, f"heritage-local-only:v1:{label}")


def require_local_demo() -> None:
    """Fail before database reads/writes on a hosted, foreign or ambiguous DB."""
    _require_isolated_local_database()
    if (
        not settings.DEBUG
        or getattr(settings, "CROWN_ENV", None) != "local"
        or str(SANDBOX_SCHOOLS["heritage-core"].id) != str(HERITAGE_ID)
        or os.environ.get("DJANGO_ENV") != "local"
        or os.environ.get("CROWN_DEMO_MODE", "").lower() != "false"
        or not bool(getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False))
        or any(os.environ.get(name) for name in (
            "WEBSITE_SITE_NAME", "AZURE_CLIENT_ID", "IDENTITY_ENDPOINT",
        ))
    ):
        raise CommandError(
            "Fictional sample seeding is restricted to canonical local Heritage, "
            "with hosted integrations disabled."
        )


def _ensure(model, label: str, defaults: dict, identity: dict):
    """Stable sample identity; reject mismatched ownership, never overwrite edits."""
    obj, created = model.objects.get_or_create(pk=fixed_id(label), defaults=defaults)
    for field, expected in identity.items():
        if getattr(obj, field) != expected:
            raise CommandError(
                f"Existing synthetic {label} has conflicting ownership; "
                "no seed writes committed."
            )
    return obj, created


@transaction.atomic
def _seed_canonical_offered_jireh(school) -> tuple[int, int]:
    """Create one fictional canonical OFFERED aid record, never a payment.

    Jireh setup reads aid.AidApplication/AidAward, not the alternate
    financial_aid summary models. Do not substitute a row-count placeholder
    for the canonical family's own-year, own-student award lineage.
    """
    # The nested helper is importable: the command/outer seeder guard alone
    # cannot authorize direct writes. Check the exact tenant before any query.
    require_local_demo()
    if (school.pk != HERITAGE_ID
            or school.name != SANDBOX_SCHOOLS["heritage-core"].name
            or not school.is_active):
        raise CommandError("Canonical Jireh preview requires the active fictional Heritage school.")
    from core.models import AcademicYear, Family, Student
    from aid.models import AidApplication, AidAward

    years = list(
        AcademicYear.objects.filter(
            school=school, is_current=True,
        ).order_by("id")[:2]
    )
    if len(years) != 1:
        raise CommandError("Canonical fictional Heritage academic year is ambiguous.")
    year = years[0]
    family, _ = _ensure(Family, "canonical-aid-family", {
        "school": school, "family_name": "Fictional Jireh Review Family",
        "status": "ACTIVE",
    }, {"school_id": HERITAGE_ID,
        "family_name": "Fictional Jireh Review Family"})
    student, _ = _ensure(Student, "canonical-aid-student", {
        "school": school, "family": family,
        "student_number": "HCA-FICTIONAL-JIREH-01",
        "first_name": "Sample", "last_name": "Jireh",
        "dob": date(2014, 3, 12), "status": "APPLICANT",
    }, {"school_id": HERITAGE_ID, "family_id": family.pk,
        "student_number": "HCA-FICTIONAL-JIREH-01"})

    apps = list(AidApplication.objects.filter(
        school=school, academic_year=year, family=family,
    ).order_by("id")[:2])
    if len(apps) > 1:
        raise CommandError("Ambiguous canonical fictional Jireh applications.")
    if apps:
        canonical_app = apps[0]
    else:
        canonical_app = AidApplication.objects.create(
            school=school, academic_year=year, family=family,
            status=AidApplication.STATUS_DRAFT,
            household_size=4, income_annual_cents=5500000,
            notes_internal="FICTIONAL HERITAGE QA application; not real eligibility.",
        )
        canonical_app.set_status(
            AidApplication.STATUS_SUBMITTED,
            details={"fictional_local_only": True, "event": "sample_intake"},
        )
    if canonical_app.status not in (
        AidApplication.STATUS_SUBMITTED,
        AidApplication.STATUS_UNDER_REVIEW,
        AidApplication.STATUS_NEEDS_INFO,
    ):
        raise CommandError("Canonical fictional Jireh application changed state.")

    awards = list(AidAward.objects.filter(
        school=school, academic_year=year, student=student,
        aid_application=canonical_app,
    ).order_by("id")[:2])
    if len(awards) > 1:
        raise CommandError("Ambiguous canonical fictional Jireh offers.")
    if awards:
        award = awards[0]
    else:
        award = AidAward.objects.create(
            school=school, academic_year=year, student=student,
            aid_application=canonical_app,
            award_type=AidAward.TYPE_NEED,
            awarded_cents=25000, recommended_award_cents=25000,
            decision_status=AidAward.DECISION_OFFERED,
        )
        award.mark_offered()  # Writes the normal AWARD_OFFERED audit event.
    if (
        award.decision_status != AidAward.DECISION_OFFERED
        or award.awarded_cents != 25000
        or award.ledger_entry_id is not None
        or award.decided_by_id is not None
    ):
        raise CommandError(
            "Fictional Jireh sample is no longer an unposted offered award."
        )
    return (
        AidApplication.objects.filter(
            school=school, pk=canonical_app.pk,
            status__in=(
                AidApplication.STATUS_SUBMITTED,
                AidApplication.STATUS_UNDER_REVIEW,
                AidApplication.STATUS_NEEDS_INFO,
            ),
        ).count(),
        AidAward.objects.filter(
            school=school, pk=award.pk, academic_year=year,
            student=student, aid_application=canonical_app,
            decision_status=AidAward.DECISION_OFFERED,
            ledger_entry__isnull=True, awarded_cents__gt=0,
        ).count(),
    )


@transaction.atomic
def seed_heritage_module_samples() -> dict[str, int]:
    """Seed bounded, idempotent samples without authorizing childcare actions."""
    require_local_demo()
    from core.models import School
    from households.models import Household, Student
    from financial_aid.models import FinancialAidApplication, AidAward
    from financial_aid.workflows import process_financial_aid_application
    from aftercare.models import AftercareEnrollment, AftercareProgramConfig
    from aftercare.daycare_models import (
        DaycareSite, DaycareRoom, DaycareProgram, DaycareChild,
        DaycareEnrollment, DaycareGuardianAuthority,
    )

    school = School.objects.select_for_update().filter(
        pk=HERITAGE_ID, is_active=True
    ).first()
    if school is None or school.name != SANDBOX_SCHOOLS["heritage-core"].name:
        raise CommandError(
            "Run the existing fictional Heritage flagship seed before "
            "adding module samples."
        )

    canonical_jireh_app_count, canonical_jireh_offer_count = (
        _seed_canonical_offered_jireh(school)
    )
    household, _ = _ensure(Household, "family", {
        "school_id": HERITAGE_ID, "name": "Fictional Five-Module QA Household",
    }, {"school_id": HERITAGE_ID})
    student, _ = _ensure(Student, "extended-care-student", {
        "school_id": HERITAGE_ID, "household": household,
        "first_name": "Sample", "last_name": "Learner", "grade_level": "3",
    }, {"school_id": HERITAGE_ID, "household_id": household.pk})

    application, _ = _ensure(FinancialAidApplication, "aid-application", {
        "school_id": HERITAGE_ID, "household_id": household.pk,
        "academic_year": "2026-27", "status": "submitted",
        "household_income": Decimal("55000.00"), "household_size": 4,
    }, {"school_id": HERITAGE_ID, "household_id": household.pk})
    # Use the actual governed recommendation workflow, not an arbitrary
    # zero-dollar award row fabricated merely to pass the count preflight.
    # This produces a provisional recommendation and matching aid audit
    # entries, never a committee-approved award or ledger/payment posting.
    if application.status == "submitted":
        result = process_financial_aid_application(application_id=application.pk)
        if result.get("status") != "success":
            raise CommandError("Synthetic financial aid recommendation was not accepted.")
    elif application.status != "in_review":
        raise CommandError("Synthetic aid application has unexpected status.")
    provisional = AidAward.objects.filter(
        school_id=HERITAGE_ID, application=application,
    )
    if provisional.count() != 1 or provisional.first().approved_by_user_id is not None:
        raise CommandError("Synthetic aid recommendation provenance is invalid.")

    AftercareProgramConfig.objects.get_or_create(school_fk=school)
    for care_session in ("AM", "PM"):
        identity = dict(
            school_fk=school, student_fk=student,
            care_session=care_session, start_date=SAMPLE_START,
        )
        matches = list(AftercareEnrollment.objects.filter(
            **identity
        ).order_by("id")[:2])
        if len(matches) > 1:
            raise CommandError(
                "Ambiguous duplicate fictional extended-care enrollment."
            )
        if not matches:
            AftercareEnrollment.objects.create(
                **identity, end_date=None,
                days_of_week=["MON", "TUE", "WED", "THU", "FRI"],
                billing_model="FLAT_MONTHLY", monthly_rate=Decimal("0.00"),
                is_active=True,
            )

    site, _ = _ensure(DaycareSite, "daycare-site", {
        "school": school, "code": "fictional-qa",
        "name": "Fictional QA Daycare Center",
        "is_active": True, "operating_mode": "INTEGRATED", "jurisdiction": "",
    }, {"school_id": HERITAGE_ID})
    # Do not assert legally verified capacity, staff ratios, or pickup grants.
    room, _ = _ensure(DaycareRoom, "daycare-room-unapproved", {
        "school": school, "site": site, "code": "policy-pending",
        "name": "Training Room - Policy Pending", "is_active": False,
        "licensed_capacity": None, "max_children_per_staff": None,
        "policy_source": "",
    }, {"school_id": HERITAGE_ID, "site_id": site.pk})
    program, _ = _ensure(DaycareProgram, "daycare-program", {
        "school": school, "site": site, "code": "DAYCARE",
        "name": "Fictional Daycare Program", "is_active": True,
    }, {"school_id": HERITAGE_ID, "site_id": site.pk})
    child, _ = _ensure(DaycareChild, "daycare-child", {
        "school": school, "site": site, "household": household,
        "first_name": "Sample", "last_name": "Preschooler",
        "date_of_birth": date(2023, 1, 1), "is_active": True,
    }, {"school_id": HERITAGE_ID, "site_id": site.pk,
        "household_id": household.pk})
    enrollment, _ = _ensure(DaycareEnrollment, "daycare-blocked-enrollment", {
        "school": school, "site": site, "child": child,
        "program": program, "room": room,
        "status": "ACTIVE", "readiness": "BLOCKED",
        "start_date": SAMPLE_START, "weekdays": [0, 1, 2, 3, 4],
    }, {"school_id": HERITAGE_ID, "site_id": site.pk,
        "child_id": child.pk, "program_id": program.pk})
    # This seed is a BLOCKED training fixture, not a grant of childcare
    # readiness. Never silently count a changed record as the original sample.
    if (
        not site.is_active
        or not program.is_active
        or not child.is_active
        or room.is_active
        or room.licensed_capacity is not None
        or room.max_children_per_staff is not None
        or room.policy_verified_by_id is not None
        or room.policy_verified_at is not None
        or enrollment.status != "ACTIVE"
        or enrollment.readiness != "BLOCKED"
        or enrollment.room_id != room.pk
        or DaycareGuardianAuthority.objects.filter(
            child=child, is_active=True,
        ).exists()
    ):
        raise CommandError(
            "Fictional Diadem blocked sample changed; manual reconciliation required."
        )
    return {
        "canonical_jireh_applications": canonical_jireh_app_count,
        "canonical_jireh_offered_awards": canonical_jireh_offer_count,
        "financial_aid_applications": FinancialAidApplication.objects.filter(
            pk=application.pk, school_id=school.pk).count(),
        "financial_aid_sample_awards": AidAward.objects.filter(
            school_id=school.pk, application=application).count(),
        "extended_care_am_enrollments": AftercareEnrollment.objects.filter(
            school_fk=school, care_session="AM", student_fk=student,
            is_active=True).count(),
        "extended_care_pm_enrollments": AftercareEnrollment.objects.filter(
            school_fk=school, care_session="PM", student_fk=student,
            is_active=True).count(),
        "diadem_blocked_active_enrollments": DaycareEnrollment.objects.filter(
            pk=enrollment.pk, school=school, status="ACTIVE",
            readiness="BLOCKED").count(),
    }
