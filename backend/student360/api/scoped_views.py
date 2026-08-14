from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Student as CoreStudent, StudentIdentityLink
from households.models import Guardian, Student
from households.scoping import get_request_school_id
from student360.api.views import StudentOverview


def _delegate_overview(request, student):
    delegate = StudentOverview()
    delegate.request = request
    delegate.args = []
    delegate.kwargs = {"student_id": student.id}
    return delegate.get(request, student_id=student.id)


def _same_school_staff(request, school_id) -> bool:
    if str(getattr(request.user, "school_id", "") or "") != str(school_id):
        return False
    staff = getattr(request.user, "staff", None)
    return bool(getattr(request.user, "is_staff", False) or (staff and str(getattr(staff, "school_id", "")) == str(school_id)))


def _resolve_verified_canonical_student(student, school_id):
    """Return canonical core.Student only for a same-school VERIFIED identity link."""
    link = (
        StudentIdentityLink.objects.select_related("core_student")
        .filter(
            compatibility_student_id=student.id,
            school_id=school_id,
            verification_status=StudentIdentityLink.STATUS_VERIFIED,
            core_student__school_id=school_id,
        )
        .first()
    )
    return link.core_student if link is not None else student


class ScopedStudentOverview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        school_id = get_request_school_id(request, required=True)
        student = Student.objects.filter(
            id=student_id,
            school_id=school_id,
            is_active=True,
            household__school_id=school_id,
            household__is_active=True,
        ).first()
        if student is not None:
            authorized = student.account_id == getattr(request.user, "id", None)
            if not authorized:
                authorized = Guardian.objects.filter(
                    account=request.user,
                    school_id=school_id,
                    household_id=student.household_id,
                ).exists()
            if not authorized:
                authorized = _same_school_staff(request, school_id)
            if not authorized:
                return Response({"detail": "Student not found."}, status=404)
            return _delegate_overview(
                request,
                _resolve_verified_canonical_student(student, school_id),
            )

        core_student = CoreStudent.objects.filter(id=student_id, school_id=school_id).first()
        if core_student is None or not _same_school_staff(request, school_id):
            return Response({"detail": "Student not found."}, status=404)
        return _delegate_overview(request, core_student)


class ScopedStudentSelfOverview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = get_request_school_id(request, required=True)
        student = Student.objects.filter(
            account=request.user,
            school_id=school_id,
            is_active=True,
            household__school_id=school_id,
            household__is_active=True,
        ).first()
        if student is None:
            return Response({"detail": "No active student profile is linked to this account."}, status=404)
        return _delegate_overview(
            request,
            _resolve_verified_canonical_student(student, school_id),
        )
