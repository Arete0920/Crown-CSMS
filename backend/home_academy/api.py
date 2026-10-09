from uuid import UUID
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from academics.models import Course, Term
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
from .integrations import (
    HomeAcademyIntegrationError,
    create_finance_obligation_for_registration,
    post_transcript_for_registration,
)
from .services import (
    apply_eligibility_to_registration,
    classify_financial_aid,
    evaluate_offering_eligibility,
)
from .tenant import school_id_from_request


def require_role(request, allowed_roles: set) -> bool:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return False

    # A selected, validated tenant is required even for platform administrators.
    # Ordinary Django staff status is never a Home Academy permission grant.
    school = getattr(request, "school", None)
    if school is None:
        return False
    if getattr(user, "is_superuser", False):
        return True

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
    academic_course_id = serializer.validated_data.get("academic_course_id")
    if academic_course_id and not Course.objects.filter(
        pk=academic_course_id, school_id=school_id
    ).exists():
        return Response(
            {"detail": "Academic course not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    academic_term_id = serializer.validated_data.get("academic_term_id")
    if academic_term_id and not Term.objects.filter(
        pk=academic_term_id, school_id=school_id
    ).exists():
        return Response(
            {"detail": "Academic term not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
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
    registration = classify_financial_aid(registration)
    return Response(OfferingEnrollmentSerializer(registration).data, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def activate_offering_enrollment(request, registration_id: int):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error
    if not require_role(request, {"admin", "registrar"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    registration = (
        OfferingEnrollment.objects.filter(pk=registration_id, school_id=school_id)
        .select_related("offering")
        .first()
    )
    if registration is None:
        return Response({"detail": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)

    if registration.status == "active":
        return Response(OfferingEnrollmentSerializer(registration).data)

    registration.admin_approved = True
    registration.save(update_fields=["admin_approved", "updated_at"])
    registration = apply_eligibility_to_registration(registration)
    if not registration.eligibility_status == "eligible":
        return Response(
            {
                "detail": "Registration is not eligible for activation.",
                "failures": registration.eligibility_failures,
            },
            status=status.HTTP_409_CONFLICT,
        )

    try:
        create_finance_obligation_for_registration(registration)
    except HomeAcademyIntegrationError as exc:
        return Response(
            {"detail": str(exc), "code": "FINANCE_INTEGRATION_BLOCKED"},
            status=status.HTTP_409_CONFLICT,
        )

    registration.refresh_from_db()
    registration.status = "active"
    registration.roster_status = "active"
    registration.save(update_fields=["status", "roster_status", "updated_at"])
    return Response(OfferingEnrollmentSerializer(registration).data)


@api_view(["POST"])
def complete_offering_enrollment(request, registration_id: int):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error
    if not require_role(request, {"admin", "registrar"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    registration = (
        OfferingEnrollment.objects.filter(pk=registration_id, school_id=school_id)
        .select_related("offering")
        .first()
    )
    if registration is None:
        return Response({"detail": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)
    if registration.status not in {"active", "completed"}:
        return Response(
            {"detail": "Registration must be active before completion."},
            status=status.HTTP_409_CONFLICT,
        )

    letter = str(request.data.get("final_letter_grade", "")).strip().upper()
    percentage = request.data.get("final_percentage")
    if registration.offering.credit_bearing and not letter:
        return Response(
            {"detail": "Final letter grade is required for credit-bearing offerings."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    registration.final_letter_grade = letter
    registration.final_percentage = percentage if percentage not in ("", None) else None
    registration.status = "completed"
    registration.roster_status = "completed"
    if registration.offering.credit_bearing and registration.offering.transcript_eligible:
        registration.transcript_posting_status = "pending_registrar"
    else:
        registration.transcript_posting_status = "not_applicable"
    registration.save(
        update_fields=[
            "final_letter_grade",
            "final_percentage",
            "status",
            "roster_status",
            "transcript_posting_status",
            "updated_at",
        ]
    )
    return Response(OfferingEnrollmentSerializer(registration).data)


@api_view(["POST"])
def post_offering_transcript(request, registration_id: int):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error
    if not require_role(request, {"admin", "registrar"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    registration = (
        OfferingEnrollment.objects.filter(pk=registration_id, school_id=school_id)
        .select_related("offering")
        .first()
    )
    if registration is None:
        return Response({"detail": "Registration not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        entry = post_transcript_for_registration(registration)
    except HomeAcademyIntegrationError as exc:
        return Response(
            {"detail": str(exc), "code": "TRANSCRIPT_INTEGRATION_BLOCKED"},
            status=status.HTTP_409_CONFLICT,
        )

    registration.refresh_from_db()
    return Response(
        {
            "registration": OfferingEnrollmentSerializer(registration).data,
            "transcript_entry_id": str(entry.id),
        }
    )


@extend_schema(responses=EligibilityResponseSerializer)
@api_view(["GET"])
def offering_eligibility(request, offering_id: int, student_id: UUID):
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
def parent_summary(request):
    school_id = school_id_from_request(request, required=True)
    module_error = require_home_academy_enabled(school_id)
    if module_error is not None:
        return module_error
    if not require_role(request, {"parent"}):
        return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    user = getattr(request, "user", None)
    guardian = getattr(user, "guardian", None)
    if (
        guardian is None
        or guardian.school_id != school_id
        or not guardian.portal_access
    ):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    students = list(
        Student.objects.filter(
            school_id=school_id,
            family_id=guardian.family_id,
            status="ACTIVE",
        ).order_by("last_name", "first_name")
    )
    student_ids = [student.id for student in students]
    enrollments = HomeAcademyEnrollment.objects.filter(
        school_id=school_id,
        student_id__in=student_ids,
        is_active=True,
    ).select_related("program")
    registrations = OfferingEnrollment.objects.filter(
        school_id=school_id,
        student_id__in=student_ids,
    ).select_related("offering")

    enrollment_by_student = {row.student_id: row for row in enrollments}
    registrations_by_student = {}
    for row in registrations:
        registrations_by_student.setdefault(row.student_id, []).append(row)

    program = HomeAcademyProgram.objects.filter(
        school_id=school_id,
        is_active=True,
    ).first()
    offerings = Offering.objects.filter(
        school_id=school_id,
        active=True,
    ).order_by("offering_type", "title")[:1000]

    return Response(
        {
            "program": HomeAcademyProgramSerializer(program).data if program else None,
            "students": [
                {
                    "id": str(student.id),
                    "name": f"{student.first_name} {student.last_name}".strip(),
                    "grade_level": (
                        student.current_grade_level.label
                        if student.current_grade_level_id
                        else ""
                    ),
                    "home_academy_enrollment": (
                        HomeAcademyEnrollmentSerializer(
                            enrollment_by_student.get(student.id)
                        ).data
                        if enrollment_by_student.get(student.id)
                        else None
                    ),
                    "registrations": OfferingEnrollmentSerializer(
                        registrations_by_student.get(student.id, []),
                        many=True,
                    ).data,
                }
                for student in students
            ],
            "offerings": OfferingSerializer(offerings, many=True).data,
        }
    )


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
