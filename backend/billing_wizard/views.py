from datetime import date
from decimal import Decimal, InvalidOperation
import json

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from core.permissions import CrownModulePermission
from rest_framework.authentication import SessionAuthentication
from crown_api.tenant_authentication import TenantJWTAuthentication
from rest_framework.response import Response
from rest_framework import status

from billing.models import InstallmentPlan
from households.scoping import get_request_school_id

from .models import BillingWizardSession
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

_AUTH = [TenantJWTAuthentication, SessionAuthentication]
_PERM = [CrownModulePermission("finance.edit", write_code="finance.edit")]

FEE_TYPES = {"REGISTRATION", "TECH", "BOOKS", "ATHLETICS", "OTHER"}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_session(session_id, school_id):
    return get_object_or_404(BillingWizardSession, id=session_id, school__id=school_id)


def _parse_date(value, field_name):
    """Parse an ISO date string; return (date_obj, None) or (None, error_str)."""
    if not value:
        return None, f"{field_name} is required"
    try:
        return date.fromisoformat(str(value)), None
    except ValueError:
        return None, f"{field_name} must be a valid ISO date (YYYY-MM-DD)"


def _parse_decimal(value, field_name, min_val=None):
    try:
        d = Decimal(str(value))
        # JSON accepts strings that Decimal parses as NaN or infinity.
        # Reject non-finite and unrepresentable monetary values before storing
        # a wizard configuration or attempting a later quantize().
        if not d.is_finite():
            return None, f"{field_name} must be a finite monetary amount"
        d = d.quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None, f"{field_name} must be a valid monetary amount"
    if min_val is not None and d < Decimal(str(min_val)):
        return None, f"{field_name} must be >= {min_val}"
    return d, None


def _validate_plan(plan, idx):
    errors = []
    if not isinstance(plan, dict):
        return [f"plans[{idx}] must be an object"]
    name = plan.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"plans[{idx}].name is required")
    try:
        count = int(plan.get("installment_count", 0))
        if count < 1:
            errors.append(f"plans[{idx}].installment_count must be >= 1")
    except (TypeError, ValueError):
        errors.append(f"plans[{idx}].installment_count must be an integer")
        count = 0

    _, date_err = _parse_date(plan.get("first_due_on"), f"plans[{idx}].first_due_on")
    if date_err:
        errors.append(date_err)

    try:
        cadence = int(plan.get("cadence_days", 30))
        if cadence < 0:
            errors.append(f"plans[{idx}].cadence_days must be >= 0")
    except (TypeError, ValueError):
        errors.append(f"plans[{idx}].cadence_days must be an integer")

    _, amt_err = _parse_decimal(plan.get("total_amount"), f"plans[{idx}].total_amount", min_val=0)
    if amt_err:
        errors.append(amt_err)

    return errors


def _validate_fee(fee, idx):
    errors = []
    if not isinstance(fee, dict):
        return [f"fees[{idx}] must be an object"]
    name = fee.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append(f"fees[{idx}].name is required")
    raw_type = fee.get("fee_type")
    fee_type = raw_type.upper() if isinstance(raw_type, str) else ""
    if fee_type not in FEE_TYPES:
        errors.append(f"fees[{idx}].fee_type must be one of {sorted(FEE_TYPES)}")
    grade_level = fee.get("grade_level")
    if grade_level is not None and not isinstance(grade_level, str):
        errors.append(f"fees[{idx}].grade_level must be a string")
    _, amt_err = _parse_decimal(fee.get("amount"), f"fees[{idx}].amount", min_val=0)
    if amt_err:
        errors.append(amt_err)
    return errors


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def create_session(request):
    school_id = get_request_school_id(request)
    from core.models import School
    school = get_object_or_404(School, id=school_id)
    session = BillingWizardSession.objects.create(
        school=school,
        created_by=request.user,
    )
    return Response(
        {"session_id": str(session.id), "status": session.status},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def configure_session(request, session_id):
    school_id = get_request_school_id(request)
    session = get_object_or_404(
        BillingWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
    )
    if session.status in (BillingWizardSession.STATUS_COMMITTED, BillingWizardSession.STATUS_VERIFIED):
        return Response(
            {"error": "Committed or verified billing wizard sessions are immutable"},
            status=status.HTTP_409_CONFLICT,
        )

    raw_term = request.data.get("term")
    term = raw_term.strip() if isinstance(raw_term, str) else ""
    if not term:
        return Response({"error": "term is required"}, status=status.HTTP_400_BAD_REQUEST)
    if len(term) > 24:
        return Response({"error": "term must be <= 24 characters"}, status=status.HTTP_400_BAD_REQUEST)

    raw_mode = request.data.get("billing_mode")
    billing_mode = raw_mode.lower() if isinstance(raw_mode, str) else ""
    valid_modes = {c[0] for c in BillingWizardSession.BILLING_MODE_CHOICES}
    if billing_mode not in valid_modes:
        return Response(
            {"error": f"billing_mode must be one of {sorted(valid_modes)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    session.term = term
    session.billing_mode = billing_mode
    session.status = BillingWizardSession.STATUS_CONFIGURED
    session.save(update_fields=["term", "billing_mode", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def save_plans(request, session_id):
    school_id = get_request_school_id(request)
    session = get_object_or_404(
        BillingWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
    )
    if session.status in (BillingWizardSession.STATUS_COMMITTED, BillingWizardSession.STATUS_VERIFIED):
        return Response(
            {"error": "Committed or verified billing wizard sessions are immutable"},
            status=status.HTTP_409_CONFLICT,
        )

    plans = request.data.get("plans")
    if not isinstance(plans, list) or len(plans) == 0:
        return Response({"error": "plans must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    for idx, plan in enumerate(plans):
        errors.extend(_validate_plan(plan, idx))
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    # Normalise
    normalised = []
    for plan in plans:
        normalised.append({
            "name": plan["name"].strip(),
            "installment_count": int(plan["installment_count"]),
            "first_due_on": str(plan["first_due_on"]),
            "cadence_days": int(plan.get("cadence_days", 30)),
            "total_amount": str(Decimal(str(plan["total_amount"])).quantize(Decimal("0.01"))),
        })

    session.plans_config = normalised
    session.status = BillingWizardSession.STATUS_PLANS_SAVED
    session.save(update_fields=["plans_config", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "plans_count": len(normalised)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def save_fees(request, session_id):
    school_id = get_request_school_id(request)
    session = get_object_or_404(
        BillingWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
    )
    if session.status in (BillingWizardSession.STATUS_COMMITTED, BillingWizardSession.STATUS_VERIFIED):
        return Response(
            {"error": "Committed or verified billing wizard sessions are immutable"},
            status=status.HTTP_409_CONFLICT,
        )

    fees = request.data.get("fees")
    if not isinstance(fees, list):
        return Response({"error": "fees must be a list"}, status=status.HTTP_400_BAD_REQUEST)

    errors = []
    for idx, fee in enumerate(fees):
        errors.extend(_validate_fee(fee, idx))
    if errors:
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

    normalised = []
    for fee in fees:
        normalised.append({
            "name": fee["name"].strip(),
            "fee_type": fee["fee_type"].upper(),
            "amount": str(Decimal(str(fee["amount"])).quantize(Decimal("0.01"))),
            "is_recurring": bool(fee.get("is_recurring", False)),
            "grade_level": (fee.get("grade_level") or "").strip() or None,
        })

    session.fees_config = normalised
    session.status = BillingWizardSession.STATUS_FEES_SAVED
    session.save(update_fields=["fees_config", "status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "fees_count": len(normalised)})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def commit_session(request, session_id):
    school_id = get_request_school_id(request)
    session = get_object_or_404(
        BillingWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
    )

    # Idempotency guard: already committed
    if session.status == BillingWizardSession.STATUS_COMMITTED:
        return Response({"session_id": str(session.id), "status": session.status, "result": session.commit_result})

    if session.status == BillingWizardSession.STATUS_VERIFIED:
        return Response({"session_id": str(session.id), "status": session.status, "result": session.commit_result})

    # confirm gate
    if request.data.get("confirm") is not True:
        return Response({"error": "confirm must be true"}, status=status.HTTP_400_BAD_REQUEST)

    # must have at least configured
    committable = {
        BillingWizardSession.STATUS_CONFIGURED,
        BillingWizardSession.STATUS_PLANS_SAVED,
        BillingWizardSession.STATUS_FEES_SAVED,
    }
    if session.status not in committable:
        return Response(
            {"error": f"session is not in a committable state (current: {session.status})"},
            status=status.HTTP_409_CONFLICT,
        )

    if not session.plans_config:
        return Response({"error": "no plans configured — save at least one plan before committing"}, status=status.HTTP_400_BAD_REQUEST)

    plans_created = []
    with transaction.atomic():
        for plan_cfg in session.plans_config:
            first_due_on = date.fromisoformat(plan_cfg["first_due_on"])
            plan, _ = InstallmentPlan.objects.get_or_create(
                school_id=school_id,
                term=session.term,
                name=plan_cfg["name"],
                defaults={
                    "installment_count": plan_cfg["installment_count"],
                    "first_due_on": first_due_on,
                    "cadence_days": plan_cfg["cadence_days"],
                },
            )
            plans_created.append({"name": plan_cfg["name"], "plan_id": str(plan.id)})

        commit_result = {
            "term": session.term,
            "billing_mode": session.billing_mode,
            "plans": plans_created,
            "fees_count": len(session.fees_config),
            "fees_config": session.fees_config,
        }
        session.commit_result = commit_result
        session.status = BillingWizardSession.STATUS_COMMITTED
        session.save(update_fields=["commit_result", "status", "updated_at"])

    return Response({"session_id": str(session.id), "status": session.status, "result": commit_result})


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET", "POST"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
@transaction.atomic
def verify_session(request, session_id):
    school_id = get_request_school_id(request)
    session = (
        get_object_or_404(
            BillingWizardSession.objects.select_for_update(), id=session_id, school_id=school_id,
        ) if request.method == "POST" else _get_session(session_id, school_id)
    )

    if session.status == BillingWizardSession.STATUS_VERIFIED:
        return Response({"session_id": str(session.id), "status": session.status, "result": session.commit_result})

    if session.status != BillingWizardSession.STATUS_COMMITTED:
        return Response(
            {"error": f"session must be committed before verifying (current: {session.status})"},
            status=status.HTTP_409_CONFLICT,
        )

    if request.method == "POST":
        session.status = BillingWizardSession.STATUS_VERIFIED
        session.save(update_fields=["status", "updated_at"])
    return Response({"session_id": str(session.id), "status": session.status, "result": session.commit_result})
