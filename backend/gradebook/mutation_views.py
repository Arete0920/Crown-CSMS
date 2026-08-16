from __future__ import annotations

from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from academics.models import Assignment, Enrollment, TeacherAssignment
from core.models import School, UserRole
from core.permissions import user_has_permission
from households.models import Student
from households.scoping import get_request_school_id

from .models import GradeEntry
from .serializers import GradeEntryUpdateSerializer
from .views import _get_section_or_404


GRADEBOOK_EDIT_PERMISSION = "gradebook.edit"


def _school_for_request(request, school_id):
    school = getattr(request, "school", None)
    if school is not None and str(getattr(school, "id", "")) == str(school_id):
        return school
    return get_object_or_404(School, pk=school_id)


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        UserRole.objects.filter(user=user, school_id=school_id).values_list(
            "role_code", flat=True
        )
    )


def _require_grade_mutation_authority(request, school_id, section) -> None:
    school = _school_for_request(request, school_id)
    if not user_has_permission(
        request.user,
        GRADEBOOK_EDIT_PERMISSION,
        school=school,
    ):
        raise PermissionDenied("Grade mutation permission denied.")

    roles = _role_codes(request.user, school_id)
    if "TEACHER" not in roles:
        return

    staff = getattr(request.user, "staff", None)
    if staff is None:
        raise Http404()
    if not TeacherAssignment.objects.filter(
        school_id=school_id,
        section=section,
        staff=staff,
    ).exists():
        raise Http404()


def _require_roster_membership(*, school_id, section, student) -> None:
    if not Enrollment.objects.filter(
        school_id=school_id,
        section=section,
        student=student,
    ).exists():
        raise ValueError("Student is not enrolled in this section.")


def _normalize_points(value):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("points_earned must be numeric or null.") from exc


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_grade_entry(request, entry_id):
    school_id = get_request_school_id(request, required=True)
    entry = get_object_or_404(
        GradeEntry.objects.select_related("section", "student"),
        id=entry_id,
        school_id=school_id,
    )

    _require_grade_mutation_authority(request, school_id, entry.section)
    try:
        _require_roster_membership(
            school_id=school_id,
            section=entry.section,
            student=entry.student,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    serializer = GradeEntryUpdateSerializer(entry, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grade_entry_bulk_upsert(request, section_id, assignment_id):
    school_id = get_request_school_id(request, required=True)
    section = _get_section_or_404(request, school_id, section_id)
    _require_grade_mutation_authority(request, school_id, section)

    assignment = get_object_or_404(
        Assignment,
        id=assignment_id,
        section=section,
        school_id=school_id,
    )

    grades = request.data.get("grades")
    if not isinstance(grades, list) or not grades:
        return Response(
            {"detail": "Payload must include non-empty 'grades' list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_rows = []
    seen_student_ids: set[str] = set()
    for index, row in enumerate(grades):
        if not isinstance(row, dict):
            return Response(
                {"detail": f"grades[{index}] must be an object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        student_id = row.get("student_id")
        if not student_id:
            return Response(
                {"detail": f"grades[{index}].student_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        normalized_student_id = str(student_id)
        if normalized_student_id in seen_student_ids:
            return Response(
                {"detail": f"Duplicate student_id at grades[{index}]."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        seen_student_ids.add(normalized_student_id)

        try:
            student = Student.objects.get(pk=student_id, school_id=school_id)
        except (Student.DoesNotExist, ValueError, TypeError):
            return Response(
                {"detail": f"grades[{index}].student_id is invalid for this school."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            _require_roster_membership(
                school_id=school_id,
                section=section,
                student=student,
            )
            points_earned = _normalize_points(row.get("points_earned"))
        except ValueError as exc:
            return Response(
                {"detail": f"grades[{index}]: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_rows.append((student, points_earned))

    created_count = 0
    updated_count = 0
    out = []

    with transaction.atomic():
        for student, points_earned in validated_rows:
            obj, was_created = GradeEntry.objects.update_or_create(
                section=section,
                student=student,
                assignment_name=assignment.name,
                defaults={
                    "assignment": assignment,
                    "school_id": school_id,
                    "points_earned": points_earned,
                    "points_possible": assignment.points_possible,
                },
            )
            if was_created:
                created_count += 1
            else:
                updated_count += 1
            out.append(
                {
                    "id": str(obj.id),
                    "student_id": str(student.id),
                    "assignment_id": str(assignment.id),
                    "points_earned": (
                        str(obj.points_earned)
                        if obj.points_earned is not None
                        else None
                    ),
                }
            )

    return Response(
        {
            "created": created_count,
            "updated": updated_count,
            "count": len(out),
            "rows": out,
        }
    )
