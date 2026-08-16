from __future__ import annotations

from django.db import transaction
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from academics.models import Assignment, Enrollment, Section, TeacherAssignment
from core.models import School, UserRole
from core.permissions import user_has_permission
from households.models import Student
from households.scoping import get_request_school_id

from .models import GradeEntry
from .serializers import GradeEntryUpdateSerializer

GRADEBOOK_EDIT_PERMISSION = "gradebook.edit"
ADMIN_GRADEBOOK_ROLES = {"HEAD_OF_SCHOOL", "REGISTRAR"}


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    user_id = getattr(user, "id", None)
    if not user_id:
        return set()
    return set(
        UserRole.objects.filter(user_id=user_id, school_id=school_id).values_list(
            "role_code", flat=True
        )
    )


def _require_gradebook_write(request, school_id, section: Section) -> set[str]:
    school = get_object_or_404(School, id=school_id)
    if not user_has_permission(
        request.user,
        GRADEBOOK_EDIT_PERMISSION,
        school=school,
    ):
        raise PermissionDenied("Grade write permission required.")

    roles = _role_codes(request.user, school_id)
    if roles.intersection(ADMIN_GRADEBOOK_ROLES):
        return roles

    if "TEACHER" not in roles:
        raise PermissionDenied("Grade write role is not permitted.")

    staff = getattr(request.user, "staff", None)
    if staff is None:
        raise Http404()
    if not TeacherAssignment.objects.filter(
        school_id=school_id,
        section=section,
        staff=staff,
    ).exists():
        raise Http404()
    return roles


def _require_roster_membership(*, school_id, section: Section, student: Student) -> None:
    if not Enrollment.objects.filter(
        school_id=school_id,
        section=section,
        student=student,
    ).exists():
        raise ValueError("Student is not enrolled in this section.")


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_grade_entry(request, entry_id):
    school_id = get_request_school_id(request, required=True)
    entry = get_object_or_404(
        GradeEntry.objects.select_related("section", "student"),
        id=entry_id,
        school_id=school_id,
    )

    _require_gradebook_write(request, school_id, entry.section)
    try:
        _require_roster_membership(
            school_id=school_id,
            section=entry.section,
            student=entry.student,
        )
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    serializer = GradeEntryUpdateSerializer(
        entry,
        data=request.data,
        partial=True,
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def grade_entry_bulk_upsert(request, section_id, assignment_id):
    school_id = get_request_school_id(request, required=True)
    section = get_object_or_404(Section, id=section_id, school_id=school_id)
    _require_gradebook_write(request, school_id, section)

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

    validated_rows: list[tuple[Student, object]] = []
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

        normalized_id = str(student_id)
        if normalized_id in seen_student_ids:
            return Response(
                {"detail": f"Duplicate student_id at grades[{index}]."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        seen_student_ids.add(normalized_id)

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
        except ValueError as exc:
            return Response(
                {"detail": f"grades[{index}]: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_rows.append((student, row.get("points_earned")))

    created_count = 0
    updated_count = 0
    output_rows = []

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
            output_rows.append(
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
            "count": len(output_rows),
            "rows": output_rows,
        }
    )
