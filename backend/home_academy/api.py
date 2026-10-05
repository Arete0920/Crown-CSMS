from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from core.models import Student
from core.permissions import user_has_permission
from subscriptions.gates import school_has_module
from .models import (
    FinancialAidRule,
    HomeAcademyEnrollment,
    HomeAcademyProgram,
    Offering,
    OfferingEnrollment,
)
from .serializers import (
    EligibilityResponseSerializer,
    FinancialAidRuleSerializer,
    HomeAcademyEnrollmentSerializer,
    HomeAcademyProgramSerializer,
    OfferingEnrollmentSerializer,
    OfferingSerializer,
)
from .services import apply_eligibility_to_registration, evaluate_offering_eligibility
from .tenant import school_id_from_request


def require_role(request, allowed_roles: set) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    school = getattr(request, "school", None)
    normalized = {str(role).lower() for role in allowed_roles}

    if "admin" in normalized and user_has_permission(user, "home_academy.edit", school=school):
        return True
    if normalized.intersection({"admin", "advisor", "registrar", "coach", "director"}):
        if user_has_permission(user, "home_academy.view", school=school):
            return True
    if "parent" in normalized and user_has_permission(user, "parent.view", school=school):
        return True

    return False


def require_home_academy_enabled(school_id):
    if school_has_module(school_id, "home_academy"):
        return None
    return Response(
        {
            "detail": "Home Academy module is not enabled for this school.",
            "code": "MODULE_NOT_ENABLED",
        },
        status=status.HTTP_403_FORBIDDEN,
    )


def canonical_student(school_id, student_id):
    return Student.objects.filter(
        pk=student_id,
        school_id=school_id,
        status="ACTIVE",
    ).select_related("family").first()


def parent_can_access_student(request, school_id, student_id) -> bool:
    user = getattr(request, "user", None)
    guardian = getattr(user, "guardian", None)
    if guardian is None:
        return False
    if guardian.school_id != school_id or not guardian.portal_access:
        return False
    return Student.objects.filter(
        pk=student_id,
        school_id=school_id,
        family_id=guardian.family_id,
        status="ACTIVE",
    ).exists()


def is_parent_only_request(request) -> bool:
    return require_role(request, {"parent"}) and not require_role(
        request, {"admin", "advisor", "registrar", "coach", "director"}
    )


@extend_schema(methods=["GET"], responses=HomeAcademyProgramSerializer)
@extend_schema(methods=["PUT"], request=HomeAcademyProgramSerializer, responses=HomeAcademyProgramSerializer)
@api_view(["GET", "PUT"])
def program_config(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error

    if request.method == "GET":
        if not require_role(request, {"admin", "advisor", "registrar", "parent"}):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        program = HomeAcademyProgram.objects.filter(school_id=school_id).first()
        if not program:
            return Response({"detail": "Home Academy program is not configured."}, status=status.HTTP_404_NOT_FOUND)
        return Response(HomeAcademyProgramSerializer(program).data)

    if not require_role(request, {"admin"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    program = HomeAcademyProgram.objects.filter(school_id=school_id).first()
    serializer = HomeAcademyProgramSerializer(program, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save(school_id=school_id)
    return Response(serializer.data, status=status.HTTP_200_OK if program else status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=HomeAcademyEnrollmentSerializer(many=True))
@extend_schema(methods=["POST"], request=HomeAcademyEnrollmentSerializer, responses=HomeAcademyEnrollmentSerializer)
@api_view(["GET", "POST"])
def enrollments(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error

    if request.method == "GET":
        if not require_role(request, {"admin", "advisor", "registrar"}):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = HomeAcademyEnrollment.objects.filter(school_id=school_id).order_by("-created_at")[:500]
        return Response(HomeAcademyEnrollmentSerializer(qs, many=True).data)

    if not require_role(request, {"admin", "registrar"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = HomeAcademyEnrollmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    student = canonical_student(school_id, serializer.validated_data["student_id"])
    if student is None:
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    program = serializer.validated_data.get("program")
    if program is not None and program.school_id != school_id:
        return Response({"detail": "Program not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer.save(school_id=school_id, household_id=student.family_id)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=OfferingSerializer(many=True))
@extend_schema(methods=["POST"], request=OfferingSerializer, responses=OfferingSerializer)
@api_view(["GET", "POST"])
def offerings(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error

    if request.method == "GET":
        if not require_role(request, {"admin", "advisor", "registrar", "parent"}):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = Offering.objects.filter(school_id=school_id, active=True).order_by("offering_type", "title")[:1000]
        return Response(OfferingSerializer(qs, many=True).data)

    if not require_role(request, {"admin"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = OfferingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    program = serializer.validated_data.get("program")
    if program is not None and program.school_id != school_id:
        return Response({"detail": "Program not found."}, status=status.HTTP_404_NOT_FOUND)
    serializer.save(school_id=school_id)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses=OfferingEnrollmentSerializer(many=True))
@extend_schema(methods=["POST"], request=OfferingEnrollmentSerializer, responses=OfferingEnrollmentSerializer)
@api_view(["GET", "POST"])
def offering_enrollments(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error

    if request.method == "GET":
        if not require_role(request, {"admin", "advisor", "registrar"}):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = OfferingEnrollment.objects.filter(school_id=school_id).select_related("offering").order_by("-created_at")[:1000]
        return Response(OfferingEnrollmentSerializer(qs, many=True).data)

    if not require_role(request, {"admin", "advisor", "registrar"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = OfferingEnrollmentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    student = canonical_student(school_id, serializer.validated_data["student_id"])
    if student is None:
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    offering = serializer.validated_data["offering"]
    if offering.school_id != school_id:
        return Response({"detail": "Offering not found."}, status=status.HTTP_404_NOT_FOUND)
    academy_enrollment = serializer.validated_data.get("home_academy_enrollment")
    if academy_enrollment is not None and (
        academy_enrollment.school_id != school_id
        or academy_enrollment.student_id != student.id
    ):
        return Response(
            {"detail": "Home Academy enrollment not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    registration = serializer.save(school_id=school_id)
    registration = apply_eligibility_to_registration(registration)
    return Response(OfferingEnrollmentSerializer(registration).data, status=status.HTTP_201_CREATED)


@extend_schema(responses=EligibilityResponseSerializer)
@api_view(["GET"])
def offering_eligibility(request, offering_id: int, student_id: int):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error
    if not require_role(request, {"admin", "advisor", "registrar", "parent"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if is_parent_only_request(request) and not parent_can_access_student(
        request, school_id, student_id
    ):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
    if canonical_student(school_id, student_id) is None:
        return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        offering = Offering.objects.get(school_id=school_id, pk=offering_id, active=True)
    except Offering.DoesNotExist:
        return Response({"detail": "Offering not found."}, status=status.HTTP_404_NOT_FOUND)

    result = evaluate_offering_eligibility(
        school_id=school_id,
        student_id=student_id,
        offering=offering,
        forms_complete=str(request.query_params.get("forms_complete", "false")).lower() == "true",
        account_current=str(request.query_params.get("account_current", "true")).lower() != "false",
        admin_approved=str(request.query_params.get("admin_approved", "false")).lower() == "true",
        coach_or_director_approved=str(request.query_params.get("coach_or_director_approved", "false")).lower() == "true",
    )
    return Response(
        {
            "eligible": result.eligible,
            "failures": result.failures,
            "seats_remaining": result.seats_remaining,
            "waitlist_available": result.waitlist_available,
        }
    )


@extend_schema(methods=["GET"], responses=FinancialAidRuleSerializer(many=True))
@extend_schema(methods=["POST"], request=FinancialAidRuleSerializer, responses=FinancialAidRuleSerializer)
@api_view(["GET", "POST"])
def financial_aid_rules(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error

    if request.method == "GET":
        if not require_role(request, {"admin", "advisor", "registrar"}):
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = FinancialAidRule.objects.filter(school_id=school_id, active=True).order_by("charge_type")
        return Response(FinancialAidRuleSerializer(qs, many=True).data)

    if not require_role(request, {"admin"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    serializer = FinancialAidRuleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save(school_id=school_id)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
def board_summary(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error
    if not require_role(request, {"admin", "registrar"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    return Response(
        {
            "programs": HomeAcademyProgram.objects.filter(school_id=school_id, is_active=True).count(),
            "active_enrollments": HomeAcademyEnrollment.objects.filter(school_id=school_id, is_active=True).count(),
            "active_offerings": Offering.objects.filter(school_id=school_id, active=True).count(),
            "pending_registrations": OfferingEnrollment.objects.filter(
                school_id=school_id,
                status__in=["requested", "pending_eligibility", "waitlisted"],
            ).count(),
        }
    )
