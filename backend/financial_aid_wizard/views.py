from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from aid.models import AidApplication, AidAuditEvent, AidAward
from core.models import AcademicYear, School, Student
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id

from .models import FinancialAidWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [JWTAuthentication, SessionAuthentication]
_VIEW_PERM = [CrownModulePermission("financial_aid.view")]
_EDIT_PERM = [CrownModulePermission("financial_aid.view", write_code="financial_aid.edit")]
BUCKET_MAP = {value.lower(): value for value, _label in AidAward.TYPE_CHOICES}
VALID_BUCKETS = set(BUCKET_MAP)


def _get_session(session_id, school_id):
    return get_object_or_404(FinancialAidWizardSession, id=session_id, school__id=school_id)


def _parse_decimal(value, field_name, min_val=None):
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None, f"{field_name} must be a valid number"
    if min_val is not None and parsed < Decimal(str(min_val)):
        return None, f"{field_name} must be >= {min_val}"
    return parsed, None


def _parse_positive_int(value, field_name):
    try:
        parsed = int(str(value).strip())
    except (TypeError, ValueError):
        return None, f"{field_name} must be a positive integer"
    if parsed <= 0:
        return None, f"{field_name} must be a positive integer"
    return parsed, None


def _currency_to_cents(amount: Decimal) -> int:
    return int((amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) * 100))


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    school = get_object_or_404(School, id=school_id)
    session = FinancialAidWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response({"session_id": str(session.id), "status": session.status}, status=status.HTTP_201_CREATED)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT_PERM)
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    aid_year = (request.data.get("aid_year") or "").strip()
    if not aid_year:
        return Response({"error": "aid_year is required"}, status=status.HTTP_400_BAD_REQUEST)
    if len(aid_year) > 24:
        return Response({"error": "aid_year must be <= 24 characters"}, status=status.HTTP_400_BAD_REQUEST)
    session.aid_year = aid_year
    session.status = FinancialAidWizardSession.STATUS_CONFIGURED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT_PERM)
def save_buckets(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status not in (
        FinancialAidWizardSession.STATUS_CONFIGURED,
        FinancialAidWizardSession.STATUS_BUCKETS_SAVED,
    ):
        return Response({"error": f"Cannot save buckets from status '{session.status}'"}, status=status.HTTP_409_CONFLICT)
    buckets = request.data.get("buckets")
    if not isinstance(buckets, list):
        return Response({"error": "buckets must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    if not buckets:
        return Response({"error": "At least one bucket is required"}, status=status.HTTP_400_BAD_REQUEST)
    errors = []
    normalised = []
    for index, bucket in enumerate(buckets):
        value = str(bucket).strip().lower()
        if value not in VALID_BUCKETS:
            errors.append(f"buckets[{index}]: '{bucket}' is not a valid bucket (must be one of {sorted(VALID_BUCKETS)})")
        elif value not in normalised:
            normalised.append(value)
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    session.active_buckets = normalised
    session.status = FinancialAidWizardSession.STATUS_BUCKETS_SAVED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "active_buckets": normalised})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT_PERM)
def stage_awards(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status not in (
        FinancialAidWizardSession.STATUS_BUCKETS_SAVED,
        FinancialAidWizardSession.STATUS_AWARDS_STAGED,
    ):
        return Response({"error": f"Cannot stage awards from status '{session.status}'"}, status=status.HTTP_409_CONFLICT)
    awards_raw = request.data.get("awards")
    if not isinstance(awards_raw, list):
        return Response({"error": "awards must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    normalised = []
    for index, award in enumerate(awards_raw):
        prefix = f"awards[{index}]"
        if not isinstance(award, dict):
            errors.append(f"{prefix}: award must be an object")
            continue

        application_id, app_error = _parse_positive_int(award.get("application_id"), f"{prefix}.application_id")
        student_id, student_error = _parse_positive_int(award.get("student_id"), f"{prefix}.student_id")
        if app_error:
            errors.append(app_error)
        if student_error:
            errors.append(student_error)
        if app_error or student_error:
            continue

        bucket = (award.get("bucket") or "").strip().lower()
        if bucket not in VALID_BUCKETS:
            errors.append(f"{prefix}: bucket '{bucket}' is not valid (must be one of {sorted(VALID_BUCKETS)})")
            continue
        if bucket not in (session.active_buckets or []):
            errors.append(f"{prefix}: bucket '{bucket}' is not active for this wizard session")
            continue

        amount, error = _parse_decimal(award.get("amount", 0), f"{prefix}.amount", min_val=0)
        if error:
            errors.append(error)
            continue

        normalised.append(
            {
                "application_id": application_id,
                "student_id": student_id,
                "bucket": bucket,
                "amount": str(amount),
                "rationale": (award.get("rationale") or "").strip(),
            }
        )

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.awards_config = normalised
    session.status = FinancialAidWizardSession.STATUS_AWARDS_STAGED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "awards_count": len(normalised)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_EDIT_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status == FinancialAidWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
    if session.status != FinancialAidWizardSession.STATUS_AWARDS_STAGED:
        return Response({"error": f"Cannot commit from status '{session.status}'"}, status=status.HTTP_409_CONFLICT)
    if not request.data.get("confirm"):
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)

    configured_awards = session.awards_config or []
    academic_year = None
    if configured_awards:
        academic_year = AcademicYear.objects.filter(school_id=school_id, name=session.aid_year).first()
        if academic_year is None:
            return Response(
                {"error": "Configured academic year must exist before awards can be committed"},
                status=status.HTTP_409_CONFLICT,
            )

    resolved_awards = []
    errors = []
    for award_data in configured_awards:
        application = AidApplication.objects.filter(
            pk=award_data["application_id"],
            school_id=school_id,
            academic_year=academic_year,
        ).first()
        if application is None:
            errors.append(f"Application {award_data['application_id']} not found for configured aid year")
            continue

        student = Student.objects.filter(
            pk=award_data["student_id"],
            school_id=school_id,
            family_id=application.family_id,
        ).first()
        if student is None:
            errors.append(
                f"Student {award_data['student_id']} does not belong to application family {application.family_id}"
            )
            continue

        resolved_awards.append((award_data, application, student, BUCKET_MAP[award_data["bucket"]]))

    if errors:
        return Response(
            {"error": "Award validation failed", "errors": errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_count = 0
    skipped_count = 0
    with transaction.atomic():
        for award_data, application, student, award_type in resolved_awards:
            existing = AidAward.objects.filter(
                school_id=school_id,
                academic_year=academic_year,
                student=student,
                aid_application=application,
                award_type=award_type,
            ).first()
            if existing is not None:
                skipped_count += 1
                continue

            amount_cents = _currency_to_cents(Decimal(award_data["amount"]))
            award = AidAward.objects.create(
                school_id=school_id,
                academic_year=academic_year,
                student=student,
                aid_application=application,
                award_type=award_type,
                awarded_cents=amount_cents,
                recommended_award_cents=amount_cents,
                decision_status=AidAward.DECISION_OFFERED,
                explanation_json={
                    "source": "financial_aid_wizard",
                    "rationale": award_data.get("rationale", ""),
                },
            )
            AidAuditEvent.log(
                school=session.school,
                entity_type=AidAuditEvent.ENTITY_AWARD,
                entity_id=award.id,
                action="AWARD_STAGED",
                actor_user=request.user if request.user.is_authenticated else None,
                details={
                    "application_id": application.id,
                    "student_id": student.id,
                    "award_type": award_type,
                    "awarded_cents": amount_cents,
                    "wizard_session_id": str(session.id),
                },
            )
            created_count += 1

        commit_result = {
            "awards_created": created_count,
            "awards_skipped": skipped_count,
            "errors": [],
        }
        session.commit_result = commit_result
        session.status = FinancialAidWizardSession.STATUS_COMMITTED
        session.save()

    return Response({"session_id": str(session.id), "status": session.status, **commit_result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_VIEW_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)
    if session.status == FinancialAidWizardSession.STATUS_VERIFIED:
        return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
    if session.status != FinancialAidWizardSession.STATUS_COMMITTED:
        return Response({"error": f"Cannot verify from status '{session.status}'"}, status=status.HTTP_409_CONFLICT)
    session.status = FinancialAidWizardSession.STATUS_VERIFIED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, **(session.commit_result or {})})
