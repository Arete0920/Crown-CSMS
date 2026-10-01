from __future__ import annotations

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from academics.models import Assignment, Enrollment, Section, TeacherAssignment
from academics.experience_access import taught_sections
from core.models import School, UserRole
from core.permissions import user_has_permission
from households.models import Student
from households.scoping import get_request_school_id

from .models import GradeEntry
from .serializers import GradeEntryUpdateSerializer


GRADE_WRITE_PERMISSION = "gradebook.edit"
GRADEBOOK_ADMIN_ROLES = {"HEAD_OF_SCHOOL", "REGISTRAR"}


def _role_codes(user, school_id) -> set[str]:
    user_id = getattr(user, "id", None)
    if not user_id:
        return set()
    return set(
        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list(
            "role_code", flat=True
        )
    )


def _require_grade_write_authority(request, school_id, section) -> None:
    school = School.objects.filter(pk=school_id).first()
    if school is None or not user_has_permission(
        request.user, GRADE_WRITE_PERMISSION, school=school
    ):
        raise PermissionDenied("Grade write permission denied.")

    roles = _role_codes(request.user, school_id)
    if roles.intersection(GRADEBOOK_ADMIN_ROLES):
        return

    if "TEACHER" not in roles:
        raise PermissionDenied("Grade write permission denied.")

    staff = getattr(request.user, "staff", None)
    if (staff is None or staff.school_id != school_id or staff.status != "ACTIVE"
        or staff.role_type != "TEACHER" or not taught_sections(request.user, school_id).filter(id=section.id).exists()):
        # Preserve tenant/section concealment for teachers without assignment.
        raise Http404()


def _section_for_write(request, school_id, section_id):
    section = get_object_or_404(Section, id=section_id, school_id=school_id)
    _require_grade_write_authority(request, school_id, section)
    return section


def _student_is_enrolled(school_id, section, student) -> bool:
    return Enrollment.objects.filter(
        school_id=school_id,
        section=section,
        student=student,
    ).exists()


def _invalid_row(index: int, detail: str = "invalid") -> Response:
    return Response(
        {"detail": f"grades[{index}] is {detail}."},
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_grade_entry(request, entry_id):
    """Mutate one grade entry under current action-level and roster authority."""
    school_id = get_request_school_id(request, required=True)
    entry = get_object_or_404(
        GradeEntry.objects.select_related("section", "student"),
        id=entry_id,
        school_id=school_id,
    )

    _require_grade_write_authority(request, school_id, entry.section)
    if not _student_is_enrolled(school_id, entry.section, entry.student):
        return Response(
            {"detail": "Grade entry student is not enrolled in the section."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = GradeEntryUpdateSerializer(entry, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grade_entry_bulk_upsert(request, section_id, assignment_id):
    """Atomically upsert assignment grades for authorized roster members only."""
    school_id = get_request_school_id(request, required=True)
    section = _section_for_write(request, school_id, section_id)
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
    seen_student_ids = set()

    # Validate the entire payload before the first mutation so one invalid row
    # rejects the whole request and no partial grade write can occur.
    for index, row in enumerate(grades):
        if not isinstance(row, dict):
            return _invalid_row(index)

        student_id = row.get("student_id")
        if not student_id:
            return _invalid_row(index, "missing student_id")

        student_key = str(student_id)
        if student_key in seen_student_ids:
            return _invalid_row(index, "a duplicate student_id")
        seen_student_ids.add(student_key)

        try:
            student = Student.objects.get(pk=student_id, school_id=school_id)
        except (Student.DoesNotExist, DjangoValidationError, ValueError, TypeError):
            return _invalid_row(index, "invalid for this section")

        if not _student_is_enrolled(school_id, section, student):
            return _invalid_row(index, "invalid for this section")

        value_serializer = GradeEntryUpdateSerializer(
            data={"points_earned": row.get("points_earned")}
        )
        if not value_serializer.is_valid():
            return Response(
                {
                    "detail": f"grades[{index}].points_earned is invalid.",
                    "errors": value_serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_rows.append(
            (student, value_serializer.validated_data.get("points_earned"))
        )

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
