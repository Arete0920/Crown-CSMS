from __future__ import annotations

from django.http import JsonResponse

from core.models import UserRole
from households.models import Guardian, Student
from households.scoping import get_request_school_id

from .transcript_views import StudentTranscriptContractView, TranscriptROView


TRANSCRIPT_PRIVILEGED_ROLES = frozenset({"HEAD_OF_SCHOOL", "REGISTRAR"})


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    user_id = getattr(user, "id", None)
    if not user_id:
        return set()
    return set(
        UserRole.objects.filter(
            user_id=user_id,
            school_id=school_id,
        ).values_list("role_code", flat=True)
    )


def _can_disclose_transcript(request, student: Student, school_id) -> bool:
    """Return True only for an explicit transcript disclosure relationship.

    Full-transcript disclosure is intentionally narrower than gradebook access:
    - registrar/head-of-school roles may read within the resolved tenant;
    - the student's explicitly linked authenticated account may read self;
    - a guardian account may read only students in that same active household;
    - superusers retain the canonical tenant resolver's explicit override authority;
    - teachers and unrelated same-school users are denied full-transcript access.
    """
    user = getattr(request, "user", None)
    if user is None or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    roles = _role_codes(user, school_id)
    if roles.intersection(TRANSCRIPT_PRIVILEGED_ROLES):
        return True

    if student.account_id == getattr(user, "id", None):
        return True

    return Guardian.objects.filter(
        account=user,
        school_id=school_id,
        household_id=student.household_id,
        household__school_id=school_id,
        household__is_active=True,
    ).exists()


class TranscriptDisclosureMixin:
    """Tenant-first, relationship-aware disclosure guard for transcript reads."""

    def get(self, request, student_id, *args, **kwargs):
        school_id = get_request_school_id(request, required=True)
        student = (
            Student.objects.filter(
                id=student_id,
                school_id=school_id,
                is_active=True,
                household__school_id=school_id,
                household__is_active=True,
            )
            .select_related("household", "account")
            .first()
        )
        if student is None or not _can_disclose_transcript(request, student, school_id):
            return JsonResponse({"detail": "Student not found."}, status=404)
        return super().get(request, student_id, *args, **kwargs)


class AuthorizedTranscriptROView(TranscriptDisclosureMixin, TranscriptROView):
    pass


class AuthorizedStudentTranscriptContractView(
    TranscriptDisclosureMixin,
    StudentTranscriptContractView,
):
    pass
