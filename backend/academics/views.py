from __future__ import annotations

from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AcademicYear, UserRole
from households.models import Guardian, Student
from households.scoping import get_request_school_id

from .models import AssignmentCategory, Course, Enrollment, Section, Term
from .serializers import (
    AcademicYearSerializer,
    CourseSerializer,
    SectionSerializer,
    StudentSerializer,
    TermSerializer,
)


def _student_display_name(student: Student) -> str:
    first = getattr(student, "first_name", "") or ""
    last = getattr(student, "last_name", "") or ""
    return " ".join(part for part in [first, last] if part).strip()


def _parse_pagination(request) -> tuple[int, int]:
    try:
        limit = int(request.query_params.get("limit", 50))
        offset = int(request.query_params.get("offset", 0))
    except ValueError:
        raise ValidationError("limit and offset must be integers")

    if limit < 1 or limit > 200 or offset < 0:
        raise ValidationError("limit must be 1..200 and offset must be >= 0")

    return limit, offset


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        UserRole.objects.filter(user=user, school_id=school_id).values_list("role_code", flat=True)
    )


def _is_staffish(user, roles: set[str]) -> bool:
    return bool(
        getattr(user, "is_staff", False)
        or getattr(user, "is_superuser", False)
        or ("HEAD_OF_SCHOOL" in roles)
    )


def _guardian_household_ids_for_user(user, school_id) -> set:
    email = (getattr(user, "email", None) or "").strip()
    if not email:
        return set()
    return set(
        Guardian.objects.filter(school_id=school_id, email__iexact=email).values_list(
            "household_id", flat=True
        )
    )


def _sections_for_access(request, school_id):
    user = getattr(request, "user", None)
    roles = _role_codes(user, school_id)

    qs = (
        Section.objects.filter(school_id=school_id)
        .select_related("course", "term_ref")
        .annotate(roster_count=Count("enrollments", distinct=True))
    )

    if _is_staffish(user, roles):
        return qs

    if "TEACHER" in roles:
        staff = getattr(user, "staff", None)
        if not staff:
            return qs.none()
        return qs.filter(teacher_assignments__staff=staff).distinct()

    if "PARENT" in roles:
        household_ids = _guardian_household_ids_for_user(user, school_id)
        if not household_ids:
            return qs.none()
        student_ids = Student.objects.filter(
            school_id=school_id, household_id__in=household_ids
        ).values_list("id", flat=True)
        return qs.filter(enrollments__student_id__in=student_ids).distinct()

    if "STUDENT" in roles:
        return qs.none()

    raise PermissionDenied("Role not permitted for academics endpoints.")


def _assert_student_in_scope_or_404(request, school_id, student_id) -> None:
    user = getattr(request, "user", None)
    roles = _role_codes(user, school_id)

    if _is_staffish(user, roles):
        if not Student.objects.filter(id=student_id, school_id=school_id).exists():
            raise Http404()
        return

    if "TEACHER" in roles:
        staff = getattr(user, "staff", None)
        if not staff:
            raise Http404()
        if not Enrollment.objects.filter(
            student_id=student_id,
            section__school_id=school_id,
            section__teacher_assignments__staff=staff,
        ).exists():
            raise Http404()
        return

    if "PARENT" in roles:
        household_ids = _guardian_household_ids_for_user(user, school_id)
        if not household_ids:
            raise Http404()
        if not Student.objects.filter(
            id=student_id, school_id=school_id, household_id__in=household_ids
        ).exists():
            raise Http404()
        return

    if "STUDENT" in roles:
        raise PermissionDenied("Student identity mapping not configured.")

    raise PermissionDenied("Role not permitted for academics endpoints.")


class PaginatedReadOnlyViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        total = qs.count()
        limit, offset = _parse_pagination(request)
        page = qs[offset : offset + limit]
        serializer = self.get_serializer(page, many=True)
        return Response(
            {
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": serializer.data,
            }
        )


class AcademicYearViewSet(PaginatedReadOnlyViewSet):
    serializer_class = AcademicYearSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = AcademicYear.objects.filter(school_id=school_id).order_by("start_date")
        if _is_staffish(user, roles):
            return qs

        sections = _sections_for_access(self.request, school_id)
        term_year_ids = Term.objects.filter(sections__in=sections).values_list(
            "academic_year_id", flat=True
        )
        return qs.filter(id__in=term_year_ids).distinct()


class TermViewSet(PaginatedReadOnlyViewSet):
    serializer_class = TermSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = Term.objects.filter(school_id=school_id).order_by("ordering", "code")

        academic_year_id = self.request.query_params.get("academic_year") or self.request.query_params.get(
            "academic_year_id"
        )
        school_year = self.request.query_params.get("school_year")
        if academic_year_id:
            qs = qs.filter(academic_year_id=academic_year_id)
        if school_year:
            qs = qs.filter(school_year=school_year)

        if _is_staffish(user, roles):
            return qs

        sections = _sections_for_access(self.request, school_id)
        return qs.filter(sections__in=sections).distinct()


class CourseViewSet(PaginatedReadOnlyViewSet):
    serializer_class = CourseSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = Course.objects.filter(school_id=school_id).order_by("code")

        academic_year_id = self.request.query_params.get("academic_year") or self.request.query_params.get(
            "academic_year_id"
        )
        term_id = self.request.query_params.get("term_id")
        term_code = self.request.query_params.get("term")

        if academic_year_id:
            qs = qs.filter(sections__term_ref__academic_year_id=academic_year_id)
        if term_id:
            qs = qs.filter(sections__term_ref_id=term_id)
        if term_code:
            qs = qs.filter(sections__term=term_code)

        if _is_staffish(user, roles):
            return qs.distinct()

        sections = _sections_for_access(self.request, school_id)
        return qs.filter(sections__in=sections).distinct()


class SectionViewSet(PaginatedReadOnlyViewSet):
    serializer_class = SectionSerializer

    def get_queryset(self):
        school_id = get_request_school_id(self.request, required=True)
        user = getattr(self.request, "user", None)
        roles = _role_codes(user, school_id)

        qs = _sections_for_access(self.request, school_id)

        academic_year_id = self.request.query_params.get("academic_year") or self.request.query_params.get(
            "academic_year_id"
        )
        term_id = self.request.query_params.get("term_id")
        term_code = self.request.query_params.get("term")
        student_id = self.request.query_params.get("student_id")
        teacher_id = self.request.query_params.get("teacher_id")

        if academic_year_id:
            qs = qs.filter(term_ref__academic_year_id=academic_year_id)
        if term_id:
            qs = qs.filter(term_ref_id=term_id)
        if term_code:
            qs = qs.filter(term=term_code)
        if student_id:
            qs = qs.filter(enrollments__student_id=student_id)
        if teacher_id:
            qs = qs.filter(teacher_assignments__staff_id=teacher_id)

        if "TEACHER" in roles and teacher_id:
            staff = getattr(user, "staff", None)
            if not staff or str(staff.id) != str(teacher_id):
                return qs.none()

        return qs.distinct()


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_sections(request, student_id):
    school_id = get_request_school_id(request, required=True)
    _assert_student_in_scope_or_404(request, school_id, student_id)

    qs = _sections_for_access(request, school_id).filter(enrollments__student_id=student_id).distinct()
    serializer = SectionSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def parent_students(request):
    school_id = get_request_school_id(request, required=True)
    user = getattr(request, "user", None)
    roles = _role_codes(user, school_id)

    if _is_staffish(user, roles):
        qs = Student.objects.filter(school_id=school_id).order_by("last_name", "first_name")
        return Response(StudentSerializer(qs, many=True).data)

    if "PARENT" not in roles:
        raise PermissionDenied("Parent role required for this endpoint.")

    household_ids = _guardian_household_ids_for_user(user, school_id)
    if not household_ids:
        return Response([])

    qs = Student.objects.filter(school_id=school_id, household_id__in=household_ids).order_by(
        "last_name", "first_name"
    )
    return Response(StudentSerializer(qs, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_roster(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _sections_for_access(request, school_id).filter(id=section_id).first()
    if not section:
        raise Http404()

    enrollments = (
        Enrollment.objects
        .filter(school_id=school_id, section_id=section.id)
        .select_related("student")
        .order_by("student__last_name", "student__first_name")
    )

    students = []
    for enrollment in enrollments:
        student = enrollment.student
        students.append({
            "student_id": str(student.id),
            "display_name": _student_display_name(student),
            "grade_level": getattr(student, "grade_level", None),
            "status": "enrolled",
        })

    return Response({
        "section_id": str(section.id),
        "count": len(students),
        "students": students,
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def section_assessments(request, section_id):
    school_id = get_request_school_id(request, required=True)
    section = _sections_for_access(request, school_id).filter(id=section_id).first()
    if not section:
        raise Http404()

    categories = (
        AssignmentCategory.objects
        .filter(school_id=school_id, section_id=section.id)
        .order_by("sort_order", "name")
    )

    items = []
    for category in categories:
        items.append({
            "section_id": str(section.id),
            "category": category.name,
            "weight": str(category.weight_percent),
            "published": category.is_active,
        })

    return Response({
        "section_id": str(section.id),
        "assessments": items,
    })
