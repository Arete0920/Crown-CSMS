from __future__ import annotations

from uuid import UUID

from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from households.models import Student
from households.scoping import get_request_school_id

from .transcript_service import (
    build_student_contract,
    build_transcript_snapshot,
    compute_section_percent,
)


def _compute_section_final_percent(school_id, section_id, student_id):
    """Compatibility wrapper for callers of the pre-refactor grading helper."""
    value = compute_section_percent(school_id, section_id, student_id)
    return float(value) if value is not None else None


def _load_student(school_id, student_id: UUID):
    student = (
        Student.objects.filter(
            pk=student_id,
            school_id=school_id,
            is_active=True,
            household__school_id=school_id,
            household__is_active=True,
        )
        .select_related("household")
        .first()
    )
    if student is None:
        return None, JsonResponse({"detail": "Student not found."}, status=404)
    return student, None


class TranscriptROView(APIView):
    """Read-only transcript summary using the canonical transcript calculation authority."""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id: UUID):
        school_id = get_request_school_id(request, required=True)
        student, error = _load_student(school_id, student_id)
        if error is not None:
            return error
        return JsonResponse(
            build_transcript_snapshot(school_id=school_id, student=student),
            status=200,
        )


class StudentTranscriptContractView(APIView):
    """Student-centric transcript contract derived from the same canonical snapshot."""

    permission_classes = [IsAuthenticated]

    def get(self, request, student_id: UUID):
        school_id = get_request_school_id(request, required=True)
        student, error = _load_student(school_id, student_id)
        if error is not None:
            return error
        snapshot = build_transcript_snapshot(school_id=school_id, student=student)
        return JsonResponse(build_student_contract(snapshot), status=200)
