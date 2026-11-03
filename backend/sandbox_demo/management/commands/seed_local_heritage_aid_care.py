"""Local-only fictional Heritage financial-aid and AM/PM source records.

Not a payment, approval, custody event, entitlement grant or browser certification.
Only run after the real flagship and verified identity-crosswalk seeds.
"""
from __future__ import annotations

import os
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from aftercare.models import AftercareEnrollment
from core.models import School, StudentIdentityLink
from financial_aid.models import AidAward, FinancialAidApplication
from sandbox_demo.catalog import SANDBOX_SCHOOLS
from sandbox_demo.management.commands.five_module_demo_preflight import (
    _require_isolated_local_database,
)


def _require_local_fixture_scope():
    _require_isolated_local_database()
    if not getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False):
        raise CommandError("Explicit fictional Heritage open-session mode is required.")
    if os.environ.get("CROWN_DEMO_MODE", "false").strip().lower() not in {"false", "0"}:
        raise CommandError("Refusing enabled payment/demo override mode.")


@transaction.atomic
def seed_heritage_aid_and_extended_care():
    """Preserve any operator-modified records; never reactivate disabled care."""
    _require_local_fixture_scope()
    spec = SANDBOX_SCHOOLS["heritage-core"]
    school = School.objects.filter(pk=spec.id, is_active=True).first()
    if school is None or school.name != spec.name:
        raise CommandError("Verified fictional Heritage school is required.")

    identity = (
        StudentIdentityLink.objects.select_related(
            "core_student", "compatibility_student__household"
        )
        .filter(
            school=school,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school=school,
            compatibility_student__school_id=school.pk,
            compatibility_student__is_active=True,
            compatibility_student__household__school_id=school.pk,
            compatibility_student__household__is_active=True,
        )
        .order_by("core_student_id")
        .first()
    )
    if identity is None:
        raise CommandError("Verified same-school fictional student crosswalk is required.")
    student = identity.compatibility_student
    household = student.household
    if (
        identity.core_student.school_id != school.pk
        or student.school_id != school.pk
        or household.school_id != school.pk
    ):
        raise CommandError("Cross-school student or household linkage refused.")

    application, _ = FinancialAidApplication.objects.get_or_create(
        school_id=school.pk, household_id=household.pk, academic_year="2026-2027",
        defaults={
            "status": "in_review",
            "household_income": Decimal("45000.00"),
            "household_size": 3,
        },
    )
    # A fictional, unapproved proposal for read-only training; no payment is posted.
    AidAward.objects.get_or_create(
        school_id=school.pk, application=application,
        defaults={
            "bucket": "need",
            "amount": Decimal("1250.00"),
            "approved_by_user_id": None,
            "rationale": (
                "FICTIONAL training recommendation ONLY; not approved, "
                "paid, allocated or disbursed."
            ),
        },
    )

    # No check-ins, releases, custody claims or tuition charges are generated.
    for session in ("AM", "PM"):
        enrollment, _ = AftercareEnrollment.objects.get_or_create(
            school_fk=school, student_fk=student, care_session=session,
            defaults={
                "start_date": date(2026, 8, 15),
                "end_date": date(2027, 6, 5),
                "days_of_week": ["MON", "TUE", "WED", "THU", "FRI"],
                "billing_model": "FLAT_MONTHLY",
                "monthly_rate": Decimal("0.00"),
                "is_active": True,
            },
        )
        if not enrollment.is_active:
            raise CommandError(
                f"Existing {session} enrollment is disabled; refusing reactivation."
            )
        if enrollment.school_fk_id != school.pk or enrollment.student_fk_id != student.pk:
            raise CommandError("Cross-school care enrollment refused.")

    return {
        "aid_applications": FinancialAidApplication.objects.filter(
            school_id=school.pk, household_id=household.pk, academic_year="2026-2027"
        ).count(),
        "fictional_nonposted_award_records": AidAward.objects.filter(
            school_id=school.pk, application=application
        ).count(),
        "before_care_enrollments": AftercareEnrollment.objects.filter(
            school_fk=school, student_fk=student, care_session="AM", is_active=True
        ).count(),
        "after_care_enrollments": AftercareEnrollment.objects.filter(
            school_fk=school, student_fk=student, care_session="PM", is_active=True
        ).count(),
    }


class Command(BaseCommand):
    help = "Local-only fictional Heritage aid and AM/PM enrollment source records."

    def handle(self, *args, **options):
        for key, value in seed_heritage_aid_and_extended_care().items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(self.style.SUCCESS(
            "Fictional source records prepared; no real award approval, "
            "money movement, care custody or functional demo certification."
        ))
