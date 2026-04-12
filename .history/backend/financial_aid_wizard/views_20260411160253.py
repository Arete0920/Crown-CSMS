import json
from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from financial_aid.models import AidAward, AidBucket
from households.scoping import get_request_school_id

from .models import FinancialAidWizardSession

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]

VALID_BUCKETS = {b.value for b in AidBucket}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(
        FinancialAidWizardSession, id=session_id, school__id=school_id
    )


def _parse_decimal(value, field_name, min_val=None):
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None, f"{field_name} must be a valid number"
    if min_val is not None and d < Decimal(str(min_val)):
        return None, f"{field_name} must be >= {min_val}"
    return d, None


# ---------------------------------------------------------------------------
# 1. Create session
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = FinancialAidWizardSession.objects.create(
        school=school,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# 2. Configure (aid_year)
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
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


# ---------------------------------------------------------------------------
# 3. Save buckets
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def save_buckets(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        FinancialAidWizardSession.STATUS_CONFIGURED,
        FinancialAidWizardSession.STATUS_BUCKETS_SAVED,
    ):
        return Response(
            {"error": f"Cannot save buckets from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    buckets = request.data.get("buckets")
    if not isinstance(buckets, list):
        return Response({"error": "buckets must be a list"}, status=status.HTTP_400_BAD_REQUEST)
    if len(buckets) == 0:
        return Response({"error": "At least one bucket is required"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    normalised = []
    for i, b in enumerate(buckets):
        b_str = str(b).strip().lower()
        if b_str not in VALID_BUCKETS:
            errors.append(f"buckets[{i}]: '{b}' is not a valid bucket (must be one of {sorted(VALID_BUCKETS)})")
        else:
            if b_str not in normalised:
                normalised.append(b_str)

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.active_buckets = normalised
    session.status = FinancialAidWizardSession.STATUS_BUCKETS_SAVED
    session.save()
    return Response({"session_id": str(session.id), "status": session.status, "active_buckets": normalised})


# ---------------------------------------------------------------------------
# 4. Stage awards
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def stage_awards(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status not in (
        FinancialAidWizardSession.STATUS_BUCKETS_SAVED,
        FinancialAidWizardSession.STATUS_AWARDS_STAGED,
    ):
        return Response(
            {"error": f"Cannot stage awards from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    awards_raw = request.data.get("awards")
    if not isinstance(awards_raw, list):
        return Response({"error": "awards must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    # Empty awards list is allowed (no awards this cycle)
    errors = []
    normalised = []
    for i, aw in enumerate(awards_raw):
        prefix = f"awards[{i}]"
        application_id = (aw.get("application_id") or "").strip() if isinstance(aw, dict) else ""
        if not application_id:
            errors.append(f"{prefix}: application_id is required")
            continue

        bucket = (aw.get("bucket") or "").strip().lower() if isinstance(aw, dict) else ""
        if bucket not in VALID_BUCKETS:
            errors.append(f"{prefix}: bucket '{bucket}' is not valid (must be one of {sorted(VALID_BUCKETS)})")
            continue

        amount_raw = aw.get("amount", 0) if isinstance(aw, dict) else 0
        amount, err = _parse_decimal(amount_raw, f"{prefix}.amount", min_val=0)
        if err:
            errors.append(err)
            continue

        rationale = (aw.get("rationale") or "").strip() if isinstance(aw, dict) else ""

        normalised.append({
            "application_id": application_id,
            "bucket": bucket,
            "amount": str(amount),
            "rationale": rationale,
        })

    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    session.awards_config = normalised
    session.status = FinancialAidWizardSession.STATUS_AWARDS_STAGED
    session.save()
    return Response({
        "session_id": str(session.id),
        "status": session.status,
        "awards_count": len(normalised),
    })


# ---------------------------------------------------------------------------
# 5. Commit
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    # Idempotency guard: already committed
    if session.status == FinancialAidWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, **session.commit_result})

    if session.status != FinancialAidWizardSession.STATUS_AWARDS_STAGED:
        return Response(
            {"error": f"Cannot commit from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    if not request.data.get("confirm"):
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)

    awards_config = session.awards_config
    if not awards_config:
        return Response({"error": "No awards to commit"}, status=status.HTTP_400_BAD_REQUEST)

    import uuid as _uuid
    from financial_aid.models import FinancialAidApplication

    created_count = 0
    skipped_count = 0
    errors = []

    with transaction.atomic():
        for aw in awards_config:
            try:
                app_id = _uuid.UUID(aw["application_id"])
                app = FinancialAidApplication.objects.get(pk=app_id, school_id=school_id)
            except (ValueError, FinancialAidApplication.DoesNotExist):
                errors.append(f"Application {aw['application_id']} not found")
                continue

            _, created = AidAward.objects.get_or_create(
                school_id=school_id,
                application=app,
                bucket=aw["bucket"],
                defaults={
                    "amount": Decimal(aw["amount"]),
                    "rationale": aw.get("rationale", ""),
                    "approved_by_user_id": request.user.id if request.user.is_authenticated else None,
                },
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

    commit_result = {
        "awards_created": created_count,
        "awards_skipped": skipped_count,
        "errors": errors,
    }
    session.commit_result = commit_result
    session.status = FinancialAidWizardSession.STATUS_COMMITTED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **commit_result,
    })


# ---------------------------------------------------------------------------
# 6. Verify
# ---------------------------------------------------------------------------

@extend_schema(tags=["Wizards"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = _get_session(session_id, school_id)

    if session.status == FinancialAidWizardSession.STATUS_VERIFIED:
        return Response({
            "session_id": str(session.id),
            "status": session.status,
            **session.commit_result,
        })

    if session.status != FinancialAidWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": f"Cannot verify from status '{session.status}'"},
            status=status.HTTP_409_CONFLICT,
        )

    session.status = FinancialAidWizardSession.STATUS_VERIFIED
    session.save()

    return Response({
        "session_id": str(session.id),
        "status": session.status,
        **session.commit_result,
    })
