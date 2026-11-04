"""Hosted buyer-school fictional Jireh Aid intake; unrelated to local-only path.

Writes only canonical school Aid applications using fixed invented scenarios.
No real financial figures, uploads, scoring, awards, or payment operations.
An authorized fictional family/guardian binding must already exist.
"""
from __future__ import annotations

from uuid import UUID

from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError, NotFound
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response

from aid.models import (
    AidApplication, AidFinancialLineItem, AidFinancialProfile,
    AidHouseholdMember,
)
from core.models import AcademicYear, Family, Student
from sandbox_demo.hosted_jireh import demo_aid_family, require_hosted_workspace

_CASES = {
    "fictional_modest": ("Fictional example A", 4_800_000, 200_000, 800_000),
    "fictional_moderate": ("Fictional example B", 8_200_000, 1_500_000, 300_000),
}


def _serialize(app, school_id, family_id):
    student_ids = list(
        AidHouseholdMember.objects.filter(
            profile_id=app.financial_profile_id,
            role=AidHouseholdMember.ROLE_STUDENT,
            student__school_id=school_id,
            student__family_id=family_id,
        ).order_by("student_id").values_list("student_id", flat=True)
    )
    return {
        "id": str(app.pk),
        "status": app.status,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "academic_year_id": str(app.academic_year_id),
        "student_ids": [str(key) for key in student_ids],
        "demo_only": True,
    }


def _readback(family, school_id):
    years = AcademicYear.objects.filter(
        school_id=school_id, is_current=True
    ).order_by("-start_date", "id")
    students = Student.objects.filter(
        school_id=school_id, family_id=family.id,
        status__in=("ACTIVE", "APPLICANT"),
    ).order_by("last_name", "first_name", "id")
    apps = AidApplication.objects.filter(
        school_id=school_id, family_id=family.pk,
        academic_year__school_id=school_id,
    ).order_by("-created_at", "-pk")
    return {
        "demo_only": True,
        "synthetic_only": True,
        "message": "Invented buyer-school application; no verified financial information or award.",
        "household": family.family_name,
        "academic_years": [{"id": str(y.id), "name": y.name} for y in years],
        "students": [
            {"id": str(s.id), "name": f"{s.first_name} {s.last_name}"}
            for s in students
        ],
        "scenarios": [{"id": k, "label": v[0]} for k, v in _CASES.items()],
        "applications": [_serialize(app, school_id, family.id) for app in apps],
    }


def _parse_submission(data, family, school_id):
    allowed = {
        "fictional_acknowledged", "scenario", "household_size",
        "academic_year_id", "student_ids",
    }
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValidationError({"detail": "Only the fixed fictional application fields are accepted."})
    if data.get("fictional_acknowledged") is not True:
        raise ValidationError({"detail": "Fictional-only acknowledgement is required."})
    scenario = data.get("scenario")
    if type(scenario) is not str or scenario not in _CASES:
        raise ValidationError({"scenario": "Choose a fixed invented scenario."})
    size = data.get("household_size")
    if type(size) is not int or not 1 <= size <= 20:
        raise ValidationError({"household_size": "Whole number from 1 to 20 required."})
    try:
        year_id = UUID(str(data.get("academic_year_id")))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValidationError({"academic_year_id": "Valid year UUID required."}) from exc
    year = AcademicYear.objects.filter(
        pk=year_id, school_id=school_id, is_current=True
    ).first()
    if year is None:
        raise NotFound("Not found.")
    values = data.get("student_ids")
    if not isinstance(values, list) or not 1 <= len(values) <= 12:
        raise ValidationError({"student_ids": "Select 1 to 12 fictional students."})
    try:
        ids = [UUID(raw) for raw in values if type(raw) is str]
    except (ValueError, TypeError, AttributeError):
        ids = []
    if len(ids) != len(values) or len(set(ids)) != len(ids):
        raise ValidationError({"student_ids": "Distinct student UUIDs are required."})
    students = list(Student.objects.filter(
        pk__in=ids, school_id=school_id, family_id=family.pk,
        status__in=("ACTIVE", "APPLICANT"),
    ))
    if len(students) != len(ids):
        raise NotFound("Not found.")
    students_by_id = {student.id: student for student in students}
    return year, [students_by_id[key] for key in ids], size, _CASES[scenario]


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def hosted_aid_family(request):
    workspace, _ = require_hosted_workspace(request, ("parent",))
    family = demo_aid_family(workspace, request.user)
    school_id = workspace.school_id
    if request.method == "GET":
        response = Response(_readback(family, school_id))
        response["Cache-Control"] = "private, no-store"
        return response

    year, students, size, case = _parse_submission(request.data, family, school_id)
    # Serializes concurrent submissions by family and prevents attaching a
    # canonical profile that might have been created elsewhere.
    with transaction.atomic():
        locked = Family.objects.select_for_update().filter(
            pk=family.pk, school_id=school_id, status="ACTIVE"
        ).first()
        if locked is None:
            raise NotFound("Not found.")
        if AidApplication.objects.filter(
            school_id=school_id, family=locked, academic_year=year,
        ).exists() or AidFinancialProfile.objects.filter(
            school_id=school_id, family=locked, academic_year=year,
        ).exists():
            response = Response(
                {"detail": "This fictional household already has an application for the year."},
                status=status.HTTP_409_CONFLICT,
            )
            response["Cache-Control"] = "private, no-store"
            return response
        profile = AidFinancialProfile.objects.create(
            school_id=school_id, family=locked, academic_year=year,
            verification_status=AidFinancialProfile.STATUS_DRAFT,
            consent_to_reuse=False,
        )
        values = (case[1], case[2], case[3])
        categories = (
            AidFinancialLineItem.CATEGORY_INCOME,
            AidFinancialLineItem.CATEGORY_ASSET,
            AidFinancialLineItem.CATEGORY_LIABILITY,
        )
        AidFinancialLineItem.objects.bulk_create([
            AidFinancialLineItem(
                profile=profile, category=category,
                subcategory="fictional_hosted_buyer",
                label="Invented scenario; not verified",
                annual_amount_cents=amount,
                source_type=AidFinancialLineItem.SOURCE_APPLICANT,
                verified=False,
            )
            for category, amount in zip(categories, values)
        ])
        AidHouseholdMember.objects.bulk_create([
            AidHouseholdMember(
                profile=profile, role=AidHouseholdMember.ROLE_STUDENT,
                student=student, first_name=student.first_name,
                last_name=student.last_name, relationship="Applicant student",
            )
            for student in students
        ])
        app = AidApplication.objects.create(
            school_id=school_id, academic_year=year, family=locked,
            financial_profile=profile, household_size=size,
            income_annual_cents=case[1], assets_cents=case[2],
            liabilities_cents=case[3], status=AidApplication.STATUS_DRAFT,
        )
        app.set_status(
            AidApplication.STATUS_SUBMITTED, actor_user=request.user,
            details={
                "source": "fictional_hosted_school_buyer",
                "fictional": True,
                "student_count": len(students),
            },
        )
    response = Response(
        {"demo_only": True, "application": _serialize(app, school_id, family.id)},
        status=status.HTTP_201_CREATED,
    )
    response["Cache-Control"] = "private, no-store"
    return response
