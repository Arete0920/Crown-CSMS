"""Local-only fictional school Jireh intake into the canonical aid application.

This endpoint is not partner-SGO intake or production family financial collection.
It accepts only fixed fictional financial scenarios; no arbitrary income/asset
figures, documents, payment information, or award approvals may be submitted.
"""

from __future__ import annotations

from uuid import UUID

from django.conf import settings
from django.core.management.base import CommandError
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from aid.models import (
    AidApplication,
    AidAuditEvent,
    AidAward,
    AidFinancialLineItem,
    AidFinancialProfile,
    AidHouseholdMember,
)
from aid.serializers import FamilyAidApplicationSerializer, FamilyAidAwardSerializer
from core.models import AcademicYear, Family, Guardian, Student
from households.scoping import get_request_school_id
from sandbox_demo.management.commands.five_module_demo_preflight import (
    _require_isolated_local_database,
)


# Values are invented examples, in cents. No actual household financial inputs
# are accepted or transmitted. Never reuse these figures as verified data.
_FICTIONAL_SCENARIOS = {
    "fictional_modest": {
        "label": "Fictional case A — illustrative modest resources",
        "income": 4_800_000,
        "assets": 200_000,
        "liabilities": 800_000,
    },
    "fictional_moderate": {
        "label": "Fictional case B — illustrative moderate resources",
        "income": 8_200_000,
        "assets": 1_500_000,
        "liabilities": 300_000,
    },
}
_MAX_STUDENTS = 12


def _local_demo_enabled() -> bool:
    if not (
        settings.DEBUG
        and getattr(settings, "CROWN_ENV", "") == "local"
        and getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False)
        and not getattr(settings, "CROWN_DEMO_MODE", False)
    ):
        return False
    # Local/debug flags and SQLite alone do not prove the database disposable.
    # Reuse the exact canonical Heritage file boundary required by demo seeding.
    try:
        _require_isolated_local_database()
    except CommandError:
        return False
    return True


def _linked_family(request, school_id):
    """Authorize the exact parent role, core guardian, family and school."""
    user = request.user
    if (
        not user.is_active
        or not user.guardian_id
        or str(user.school_id) != str(school_id)
        or not user.roles.filter(school_id=school_id, role_code="PARENT").exists()
    ):
        return None

    guardian = (
        Guardian.objects.select_related("family")
        .filter(
            pk=user.guardian_id,
            school_id=school_id,
            family__school_id=school_id,
            family__status="ACTIVE",
        )
        .first()
    )
    return guardian.family if guardian else None


def _serialize_application(application, *, family, school_id):
    student_ids = []
    if application.financial_profile_id:
        student_ids = [
            str(student_id)
            for student_id in (
                AidHouseholdMember.objects.filter(
                    profile_id=application.financial_profile_id,
                    role=AidHouseholdMember.ROLE_STUDENT,
                    student__school_id=school_id,
                    student__family_id=family.id,
                )
                .order_by("student__last_name", "student__first_name", "student_id")
                .values_list("student_id", flat=True)
            )
        ]

    # An award can only be shown to its linked family and linked application.
    # The allowlisted serializer omits scoring, rationale and ledger linkage.
    awards = AidAward.objects.filter(
        school_id=school_id,
        academic_year_id=application.academic_year_id,
        aid_application=application,
        student__school_id=school_id,
        student__family_id=family.id,
    ).order_by("-created_at")

    return {
        **FamilyAidApplicationSerializer(application).data,
        "academic_year_name": application.academic_year.name,
        "student_ids": student_ids,
        "awards": FamilyAidAwardSerializer(awards, many=True).data,
    }


def _readback(family, school_id):
    years = AcademicYear.objects.filter(
        school_id=school_id, is_current=True
    ).order_by("-start_date", "id")
    students = Student.objects.filter(
        school_id=school_id, family_id=family.id,
        family__school_id=school_id, status__in=("ACTIVE", "APPLICANT"),
    ).order_by("last_name", "first_name", "id")
    applications = (
        AidApplication.objects.select_related("academic_year", "financial_profile")
        .filter(
            school_id=school_id,
            family_id=family.id,
            academic_year__school_id=school_id,
        )
        .order_by("-created_at")
    )

    return {
        "demo_only": True,
        "message": "Fictional local-school demonstration; no real financial application or transaction.",
        "household_name": family.family_name,
        "academic_years": [{"id": str(year.id), "name": year.name} for year in years],
        "students": [
            {"id": str(student.id), "name": f"{student.first_name} {student.last_name}"}
            for student in students
        ],
        "scenarios": [
            {"id": code, "label": case["label"]}
            for code, case in _FICTIONAL_SCENARIOS.items()
        ],
        "applications": [
            _serialize_application(application, family=family, school_id=school_id)
            for application in applications
        ],
    }


def _submission_fields(data, *, family, school_id):
    if not isinstance(data, dict):
        return None, Response(
            {"detail": "Expected a JSON object."}, status=status.HTTP_400_BAD_REQUEST
        )
    if data.get("fictional_acknowledged") is not True:
        return None, Response(
            {"detail": "Confirm that the application uses only fictional demonstration information."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    permitted = {
        "fictional_acknowledged", "scenario", "household_size",
        "academic_year_id", "student_ids",
    }
    if set(data) - permitted:
        return None, Response(
            {"detail": "Unsupported fields. Do not submit financial or personal information."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    scenario_code = data.get("scenario")
    case = _FICTIONAL_SCENARIOS.get(scenario_code) if type(scenario_code) is str else None
    if case is None:
        return None, Response(
            {"detail": "Select one of the fixed fictional scenarios."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    size = data.get("household_size")
    if type(size) is not int or not 1 <= size <= 20:
        return None, Response(
            {"detail": "Household size must be a whole number from 1 to 20."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        year_id = UUID(str(data.get("academic_year_id")))
    except (TypeError, ValueError, AttributeError):
        return None, Response(
            {"detail": "Select a valid academic year."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    year = AcademicYear.objects.filter(
        pk=year_id, school_id=school_id, is_current=True
    ).first()
    if year is None:
        return None, Response(
            {"detail": "The academic year is not available."},
            status=status.HTTP_404_NOT_FOUND,
        )

    raw_students = data.get("student_ids")
    if not isinstance(raw_students, list) or not 1 <= len(raw_students) <= _MAX_STUDENTS:
        return None, Response(
            {"detail": "Select 1 to 12 applicant students."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        student_ids = [UUID(value) for value in raw_students if type(value) is str]
    except (TypeError, ValueError, AttributeError):
        student_ids = []
    if len(student_ids) != len(raw_students) or len(set(student_ids)) != len(student_ids):
        return None, Response(
            {"detail": "Student selections must be distinct valid identifiers."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    students = list(
        Student.objects.filter(
            pk__in=student_ids,
            school_id=school_id,
            family_id=family.id,
            family__school_id=school_id,
            status__in=("ACTIVE", "APPLICANT"),
        )
    )
    if len(students) != len(student_ids):
        # No foreign-household or foreign-school student names are disclosed.
        return None, Response(
            {"detail": "Applicant student not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    by_id = {student.id: student for student in students}
    return {
        "year": year,
        "students": [by_id[student_id] for student_id in student_ids],
        "scenario": case,
        "size": size,
    }, None


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def family_demo_intake(request):
    """Parent-side fictional application, never a live financial collection form."""
    if not _local_demo_enabled():
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    school_id = get_request_school_id(request)
    family = _linked_family(request, school_id)
    if family is None:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(_readback(family, school_id))

    parsed, error = _submission_fields(request.data, family=family, school_id=school_id)
    if error is not None:
        return error

    # Lock one existing family row to serialize competing school/year requests.
    # No new model, payment record, award decision or external API call is created.
    with transaction.atomic():
        locked_family = Family.objects.select_for_update().get(
            pk=family.pk, school_id=school_id, status="ACTIVE"
        )
        existing = AidApplication.objects.filter(
            school_id=school_id,
            family_id=locked_family.id,
            academic_year_id=parsed["year"].id,
        ).exists()
        if existing:
            return Response(
                {"detail": "A family application already exists for this academic year."},
                status=status.HTTP_409_CONFLICT,
            )
        # A previously entered canonical profile must never be silently
        # overwritten or attached to a demonstration application.
        if AidFinancialProfile.objects.filter(
            school_id=school_id,
            family_id=locked_family.id,
            academic_year_id=parsed["year"].id,
        ).exists():
            return Response(
                {"detail": "A financial profile already exists for this academic year."},
                status=status.HTTP_409_CONFLICT,
            )

        case = parsed["scenario"]
        profile = AidFinancialProfile.objects.create(
            school_id=school_id,
            family=locked_family,
            academic_year=parsed["year"],
            verification_status=AidFinancialProfile.STATUS_DRAFT,
            consent_to_reuse=False,
        )
        AidFinancialLineItem.objects.bulk_create(
            [
                AidFinancialLineItem(
                    profile=profile,
                    category=category,
                    subcategory="fictional_local_demo",
                    label="Fictional example; not verified",
                    annual_amount_cents=case[field],
                    source_type=AidFinancialLineItem.SOURCE_APPLICANT,
                    verified=False,
                )
                for category, field in (
                    (AidFinancialLineItem.CATEGORY_INCOME, "income"),
                    (AidFinancialLineItem.CATEGORY_ASSET, "assets"),
                    (AidFinancialLineItem.CATEGORY_LIABILITY, "liabilities"),
                )
            ]
        )
        AidHouseholdMember.objects.bulk_create(
            [
                AidHouseholdMember(
                    profile=profile,
                    role=AidHouseholdMember.ROLE_STUDENT,
                    student=student,
                    first_name=student.first_name,
                    last_name=student.last_name,
                    relationship="Applicant student",
                )
                for student in parsed["students"]
            ]
        )
        application = AidApplication.objects.create(
            school_id=school_id,
            academic_year=parsed["year"],
            family=locked_family,
            financial_profile=profile,
            household_size=parsed["size"],
            income_annual_cents=case["income"],
            assets_cents=case["assets"],
            liabilities_cents=case["liabilities"],
            status=AidApplication.STATUS_DRAFT,
        )
        application.set_status(
            AidApplication.STATUS_SUBMITTED,
            actor_user=request.user,
            details={
                "source": "fictional_local_school_family_intake",
                "fictional": True,
                "student_count": len(parsed["students"]),
            },
        )

    return Response(
        {
            "demo_only": True,
            "application": _serialize_application(
                application, family=family, school_id=school_id
            ),
        },
        status=status.HTTP_201_CREATED,
    )
