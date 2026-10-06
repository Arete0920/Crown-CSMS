from __future__ import annotations

# pyright: reportMissingImports=false, reportMissingModuleSource=false, reportMissingTypeStubs=false, reportMissingParameterType=false, reportMissingTypeArgument=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false, reportUnknownParameterType=false, reportAttributeAccessIssue=false, reportOptionalMemberAccess=false, reportIndexIssue=false, reportGeneralTypeIssues=false

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
import logging
import os
import uuid
from typing import Any, TypedDict, cast

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from django.db.models import Count, Min
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from core.models import AcademicYear, School
from crown_api.tenant import resolve_tenant_school_id
from households.models import Household
from .models import (
    Application,
    Applicant,
    ApplicationEvent,
    ApplicationChecklistItem,
    ApplicationChecklistDocument,
    ChecklistItemStatus,
    EnrollmentContract,
    EnrollmentContractStatus,
)
from .aid_projection import build_award_summary_by_household
from .serializers import (
    AdmissionsContractAmendResponseSerializer,
    AdmissionsContractDetailResponseSerializer,
    AdmissionsContractUpdateResponseSerializer,
    AdmissionsDrilldownResponseSerializer,
    AdmissionsEnrollmentStateResponseSerializer,
    AdmissionsEventReplayResponseSerializer,
    AdmissionsPublicConfigResponseSerializer,
    AdmissionsSubmitResponseSerializer,
)


logger = logging.getLogger(__name__)


STAGES = [
    "inquiry",
    "tour_scheduled",
    "tour_completed",
    "application_started",
    "application_submitted",
    "in_review",
    "accepted",
    "waitlisted",
    "declined",
    "enrolled",
]

WORKFLOW_STAGE_PRIORITY = [
    "application_submitted",
    "in_review",
    "accepted",
    "waitlisted",
    "tour_scheduled",
    "tour_completed",
    "application_started",
    "inquiry",
    "enrolled",
    "declined",
]

CONTRACT_NOT_STARTED = "not_started"
CONTRACT_SENT = "sent"
CONTRACT_SIGNED = "signed"
CONTRACT_COUNTERSIGNED = "countersigned"
CONTRACT_NOT_APPLICABLE = "not_applicable"

DEPOSIT_PENDING = "pending"
DEPOSIT_INVOICED = "invoiced"
DEPOSIT_PAID = "paid"
DEPOSIT_WAIVED = "waived"
DEPOSIT_NOT_APPLICABLE = "not_applicable"

CONTRACT_RECORD_STATUS_MAP = {
    CONTRACT_NOT_STARTED: EnrollmentContractStatus.DRAFT,
    CONTRACT_SENT: EnrollmentContractStatus.ISSUED,
    CONTRACT_SIGNED: EnrollmentContractStatus.SIGNED,
    CONTRACT_COUNTERSIGNED: EnrollmentContractStatus.COUNTERSIGNED,
    CONTRACT_NOT_APPLICABLE: EnrollmentContractStatus.DRAFT,
}

CONTRACT_TOTAL_KEYS = (
    "gross_tuition_cents",
    "fees_cents",
    "discounts_cents",
    "aid_cents",
    "scholarships_cents",
    "esa_voucher_tax_credit_cents",
    "donor_assistance_cents",
    "deposit_cents",
    "amount_due_today_cents",
    "net_family_obligation_cents",
)

ENROLLMENT_STATE_EVENT_TYPE = "enrollment_state_updated"
ENROLLMENT_CONFIRMED_EVENT_TYPE = "enrollment_confirmed"
CLASSROOM_READINESS_EVENT_TYPE = "classroom_readiness_completed"
PARENT_PORTAL_ACTIVATED_EVENT_TYPE = "parent_portal_activated"
PERMISSION_DENIED_DETAIL = "Permission denied."
APPLICATION_NOT_FOUND_DETAIL = "Application not found."
ADMISSIONS_VIEW_PERMISSION = "admissions.view"
ADMISSIONS_EDIT_PERMISSION = "admissions.edit"

CONTRACT_TRANSITIONS: dict[str, set[str]] = {
    CONTRACT_NOT_STARTED: {CONTRACT_SENT},
    CONTRACT_SENT: {CONTRACT_SIGNED},
    CONTRACT_SIGNED: {CONTRACT_COUNTERSIGNED},
    CONTRACT_COUNTERSIGNED: set(),
    CONTRACT_NOT_APPLICABLE: set(),
}

DEPOSIT_TRANSITIONS: dict[str, set[str]] = {
    DEPOSIT_PENDING: {DEPOSIT_INVOICED, DEPOSIT_WAIVED},
    DEPOSIT_INVOICED: {DEPOSIT_PAID, DEPOSIT_WAIVED},
    DEPOSIT_PAID: set(),
    DEPOSIT_WAIVED: set(),
    DEPOSIT_NOT_APPLICABLE: set(),
}

WORKFLOW_STAGE_GUIDANCE = {
    "inquiry": {
        "label": "Inquiry and Exploration",
        "family_next_step": "Schedule a tour or discovery conversation and confirm the best contact path for follow-up.",
        "staff_next_step": "Assign an admissions owner, send the welcome guidance, and present the next visible action.",
        "target_sla": "First response within 1 business day",
    },
    "tour_scheduled": {
        "label": "Tour and Engagement",
        "family_next_step": "Attend the scheduled campus visit and review the mission-fit conversation prompts.",
        "staff_next_step": "Prepare visit follow-up, reminders, and event attendance capture.",
        "target_sla": "Tour follow-up within 1 business day",
    },
    "tour_completed": {
        "label": "Post-Visit Follow-up",
        "family_next_step": "Begin the application while the visit details and next questions are still fresh.",
        "staff_next_step": "Send personalized follow-up and move the family into application-start nudges.",
        "target_sla": "Application prompt within 1 business day",
    },
    "application_started": {
        "label": "Application In Progress",
        "family_next_step": "Complete remaining sections, save progress, and prepare required documents.",
        "staff_next_step": "Monitor inactivity and keep missing items and next actions visible.",
        "target_sla": "Inactivity outreach within 3 days",
    },
    "application_submitted": {
        "label": "Application Submitted",
        "family_next_step": "Watch for checklist updates, document requests, and interview scheduling instructions.",
        "staff_next_step": "Complete file review intake, assign ownership, and trigger milestone communications.",
        "target_sla": "Review and decision within 24 hours",
    },
    "in_review": {
        "label": "Mission Alignment and Review",
        "family_next_step": "Monitor the portal for file-completion requests and interview or shadow-day scheduling.",
        "staff_next_step": "Advance file review, close missing items, and prepare the discernment conversation.",
        "target_sla": "Decision target within 24 hours",
    },
    "accepted": {
        "label": "Accepted to Enrollment Conversion",
        "family_next_step": "Complete enrollment acceptance, deposit, and onboarding checklist items in the same journey thread.",
        "staff_next_step": "Support conversion, confirm deposit progress, and preserve SIS continuity.",
        "target_sla": "Enrollment follow-up within 2 business days",
    },
    "waitlisted": {
        "label": "Waitlist Governance",
        "family_next_step": "Review the status center for timeline visibility and the next expected decision update.",
        "staff_next_step": "Maintain waitlist cadence and send clear expectation updates.",
        "target_sla": "Waitlist update within 5 business days",
    },
    "declined": {
        "label": "Decision Closed",
        "family_next_step": "Contact admissions if you need clarification or future-cycle guidance.",
        "staff_next_step": "Close the file with reason capture and audit-complete communication.",
        "target_sla": "Decision notice complete",
    },
    "enrolled": {
        "label": "Enrollment and Onboarding",
        "family_next_step": "Complete onboarding, orientation, and readiness tasks in the portal.",
        "staff_next_step": "Transition the family into onboarding and confirm record continuity.",
        "target_sla": "Onboarding kickoff within 1 business day",
    },
}

SOURCES = [
    "church_referral",
    "facebook",
    "instagram",
    "google",
    "direct_mail_qr",
    "website",
    "word_of_mouth",
    "other",
]

APPLICATION_FEE_USD = Decimal("85.00")
FINANCIAL_AID_FEE_USD = Decimal(str(os.getenv("ADMISSIONS_FINANCIAL_AID_FEE_USD", "35.00")))
ENROLLMENT_FEE_USD = Decimal(str(os.getenv("ADMISSIONS_ENROLLMENT_FEE_USD", "250.00")))
APPLICATION_FEE_CURRENCY = "USD"
PAYMENT_INTENT_ENDPOINT = "/api/finance/payments/intent/"
SUBMIT_IP_RATE_LIMIT = 30
SUBMIT_IP_RATE_WINDOW_SECONDS = 15 * 60
SUBMIT_EMAIL_RATE_LIMIT = 6
SUBMIT_EMAIL_RATE_WINDOW_SECONDS = 60 * 60
ADMISSIONS_ASSESSMENT_REQUIRED = str(os.getenv("ADMISSIONS_ASSESSMENT_REQUIRED", "1")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ASSESSMENT_SCHEDULING_TARGET_SLA = "Within 3-5 business days"
REVIEW_DECISION_SLA_TEXT = "Within 24 hours"

ACADEMIC_OFFICE = "Academic Office"
FRONT_OFFICE = "Front Office"
NURSE_OFFICE = "Nurse Office"


class ChecklistRequiredItemDef(TypedDict):
    key: str
    title: str
    office: str
    owner: str
    due_days: int
    depends_on: list[str]
    parent_visible: bool
    reminder_days: list[int]
    document_flag: str

CHECKLIST_REQUIRED_ITEMS: list[ChecklistRequiredItemDef] = [
    {
        "key": "transcript",
        "title": "Official Transcript",
        "office": ACADEMIC_OFFICE,
        "owner": "Admissions Records",
        "due_days": 5,
        "depends_on": [],
        "parent_visible": True,
        "reminder_days": [3, 7],
        "document_flag": "transcriptReady",
    },
    {
        "key": "recommendations",
        "title": "Teacher Recommendations",
        "office": ACADEMIC_OFFICE,
        "owner": "Admissions Records",
        "due_days": 7,
        "depends_on": ["transcript"],
        "parent_visible": True,
        "reminder_days": [3, 7],
        "document_flag": "recommendationsReady",
    },
    {
        "key": "pastor_reference",
        "title": "Pastor/Church Reference",
        "office": FRONT_OFFICE,
        "owner": "Admissions Team",
        "due_days": 7,
        "depends_on": ["transcript"],
        "parent_visible": True,
        "reminder_days": [3, 7],
        "document_flag": "pastorReferenceReady",
    },
    {
        "key": "immunization",
        "title": "Immunization Records",
        "office": NURSE_OFFICE,
        "owner": "Health Office",
        "due_days": 10,
        "depends_on": ["transcript"],
        "parent_visible": True,
        "reminder_days": [5, 10],
        "document_flag": "immunizationReady",
    },
]


def _application_fee_required() -> bool:
    return APPLICATION_FEE_USD > Decimal("0")


def _financial_aid_fee_required(data: "AdmissionsSubmitData") -> bool:
    intent = str((data.financial_aid_interest or {}).get("intent") or "").strip().lower()
    return FINANCIAL_AID_FEE_USD > Decimal("0") and intent == "applying"


def _enrollment_fee_required() -> bool:
    return ENROLLMENT_FEE_USD > Decimal("0")


def _child_discount_percent(child_index: int) -> int:
    if child_index <= 1:
        return 0
    if child_index == 2:
        return 25
    if child_index == 3:
        return 50
    if child_index == 4:
        return 75
    return 100


def _apply_child_discount(base_amount: Decimal, child_index: int) -> Decimal:
    discount_percent = Decimal(_child_discount_percent(child_index))
    multiplier = Decimal("1") - (discount_percent / Decimal("100"))
    discounted = (base_amount * multiplier).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return max(discounted, Decimal("0.00"))


def _fee_rows_for_household(data: "AdmissionsSubmitData", application_ids: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    student_count = max(len(application_ids), len(data.students or []))
    for child_index in range(1, student_count + 1):
        app_id = application_ids[child_index - 1] if child_index - 1 < len(application_ids) else None
        app_fee = _apply_child_discount(APPLICATION_FEE_USD, child_index) if _application_fee_required() else Decimal("0.00")
        aid_fee = _apply_child_discount(FINANCIAL_AID_FEE_USD, child_index) if _financial_aid_fee_required(data) else Decimal("0.00")
        enrollment_fee = _apply_child_discount(ENROLLMENT_FEE_USD, child_index) if _enrollment_fee_required() else Decimal("0.00")
        rows.append(
            {
                "child_index": child_index,
                "application_id": app_id,
                "discount_percent": _child_discount_percent(child_index),
                "application_fee": str(app_fee),
                "financial_aid_fee": str(aid_fee),
                "enrollment_fee": str(enrollment_fee),
                "total": str((app_fee + aid_fee + enrollment_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)),
            }
        )
    return rows


def _application_fee_config() -> dict[str, Any]:
    return {
        "required": _application_fee_required(),
        "amount": str(APPLICATION_FEE_USD),
        "currency": APPLICATION_FEE_CURRENCY,
        "discount_policy": {
            "description": "2nd child 25% off, 3rd child 50% off, 4th child 75% off, 5th+ free",
            "tiers": [
                {"child_index": 1, "discount_percent": 0},
                {"child_index": 2, "discount_percent": 25},
                {"child_index": 3, "discount_percent": 50},
                {"child_index": 4, "discount_percent": 75},
                {"child_index": 5, "discount_percent": 100, "applies_to": "and_above"},
            ],
        },
    }


def _financial_aid_fee_config(data: "AdmissionsSubmitData") -> dict[str, Any]:
    return {
        "required": _financial_aid_fee_required(data),
        "amount": str(FINANCIAL_AID_FEE_USD),
        "currency": APPLICATION_FEE_CURRENCY,
    }


def _enrollment_fee_config() -> dict[str, Any]:
    return {
        "required": _enrollment_fee_required(),
        "amount": str(ENROLLMENT_FEE_USD),
        "currency": APPLICATION_FEE_CURRENCY,
    }


def _is_graph_email_configured() -> bool:
    return bool(
        (
            os.getenv("GRAPH_TENANT_ID")
            and os.getenv("GRAPH_CLIENT_ID")
            and os.getenv("GRAPH_CLIENT_SECRET")
        )
        or (
            os.getenv("AZURE_TENANT_ID")
            and os.getenv("AZURE_CLIENT_ID")
            and os.getenv("AZURE_CLIENT_SECRET")
        )
    )


def _is_sharepoint_configured() -> bool:
    return bool(os.getenv("M365_SHAREPOINT_SITE_ID") or os.getenv("M365_DEFAULT_DRIVE_ID"))


def _is_sms_configured() -> bool:
    return str(os.getenv("COMMS_SMS_ENABLED", "0")).strip().lower() in {"1", "true", "yes", "on"}


def _build_contract_m365_handoff(*, application_ids: list[str]) -> dict[str, Any]:
    return {
        "enabled": _is_graph_email_configured() and _is_sharepoint_configured(),
        "provider": "microsoft_365",
        "template": {
            "name": "Enrollment Contract Standard",
            "autopopulate_fields": [
                "guardian_names",
                "guardian_emails",
                "student_names",
                "campus",
                "start_term",
                "fees_per_child",
                "discount_schedule",
                "financial_aid_intent",
                "contract_totals",
            ],
        },
        "channels": {
            "outlook_email": _is_graph_email_configured(),
            "sharepoint_packet": _is_sharepoint_configured(),
            "teams_notification": _is_graph_email_configured(),
        },
        "application_ids": application_ids,
    }


def _decision_deadline_iso() -> str:
    return (timezone.now() + timedelta(hours=24)).isoformat()


def _queue_outbox_message(*, outbox_model: Any, idempotency_key: str, school_id: str, channel: str, to_value: str, subject: str, body: str) -> None:
    outbox_model.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "school_id": school_id,
            "channel": channel,
            "to": to_value,
            "subject": subject,
            "body": body,
        },
    )


def _queue_guardian_messages(
    *,
    outbox_model: Any,
    school_value: str,
    app_ref: str,
    guardian: dict[str, Any],
    guardian_index: int,
    email_enabled: bool,
    sms_enabled: bool,
    stage_token: str,
) -> tuple[int, int]:
    email = str(guardian.get("email") or "").strip().lower()
    phone = str(guardian.get("phone") or "").strip()
    email_queued = 0
    sms_queued = 0

    if email and email_enabled:
        _queue_outbox_message(
            outbox_model=outbox_model,
            idempotency_key=f"admissions:{app_ref}:{stage_token}:guardian:{guardian_index}:email",
            school_id=school_value,
            channel="EMAIL",
            to_value=email,
            subject="Admissions Update: Application Received",
            body=(
                "Your application was received. Review and decision target is within 24 hours. "
                "You will continue to receive updates by email and text."
            ),
        )
        email_queued = 1

    if phone and sms_enabled:
        _queue_outbox_message(
            outbox_model=outbox_model,
            idempotency_key=f"admissions:{app_ref}:{stage_token}:guardian:{guardian_index}:sms",
            school_id=school_value,
            channel="SMS",
            to_value=phone,
            subject="",
            body="CROWN Admissions: your application was received. Review and decision target is within 24 hours.",
        )
        sms_queued = 1

    return email_queued, sms_queued


def _queue_family_communications(
    *,
    school_id: Any,
    guardians: list[dict[str, Any]],
    application_ids: list[str],
    correlation_id: str,
    stage_token: str = "application_submitted",
) -> dict[str, Any]:
    email_enabled = _is_graph_email_configured()
    sms_enabled = _is_sms_configured()
    summary: dict[str, Any] = {
        "email": {"queued": 0, "enabled": email_enabled},
        "sms": {"queued": 0, "enabled": sms_enabled},
        "status": "not_configured",
        "correlation_id": correlation_id,
    }

    try:
        from comms.models import OutboxMessage  # noqa: PLC0415
    except Exception:
        summary["status"] = "outbox_unavailable"
        return summary

    app_ref = application_ids[0] if application_ids else "unknown"
    school_value = str(school_id)

    for index, guardian in enumerate(guardians or []):
        email_queued, sms_queued = _queue_guardian_messages(
            outbox_model=OutboxMessage,
            school_value=school_value,
            app_ref=app_ref,
            guardian=guardian,
            guardian_index=index,
            email_enabled=email_enabled,
            sms_enabled=sms_enabled,
            stage_token=stage_token,
        )
        summary["email"]["queued"] += email_queued
        summary["sms"]["queued"] += sms_queued

    has_queued = summary["email"]["queued"] > 0 or summary["sms"]["queued"] > 0
    if has_queued:
        summary["status"] = "queued"
    elif summary["email"]["enabled"] or summary["sms"]["enabled"]:
        summary["status"] = "enabled_no_recipients"
    else:
        summary["status"] = "not_configured"

    return summary


def _assessment_interview_config() -> dict[str, Any]:
    return {
        "required": ADMISSIONS_ASSESSMENT_REQUIRED,
        "target_sla": ASSESSMENT_SCHEDULING_TARGET_SLA,
        "preferred_tour_windows": ["Weekday mornings", "Weekday afternoons", "Evenings", "Flexible"],
        "preferred_interview_modes": ["In person", "Video call", "Phone", "No preference"],
    }


def _normalize_source(value: str | None) -> str:
    raw = (value or "").strip().lower().replace("-", "_").replace(" ", "_")
    mapping = {
        "church_referral": "church_referral",
        "church": "church_referral",
        "current_family": "word_of_mouth",
        "friend_or_colleague": "word_of_mouth",
        "word_of_mouth": "word_of_mouth",
        "social_media": "facebook",
        "search_engine": "google",
        "community_event": "website",
        "website": "website",
    }
    normalized = mapping.get(raw, "other")
    return normalized if normalized in SOURCES else "other"


def _validation_error(detail: str, code: str = "invalid_request", correlation_id: str | None = None) -> Response:
    payload = {
        "detail": detail,
        "message": detail,
        "code": code,
    }
    if correlation_id:
        payload["correlation_id"] = correlation_id
    return Response(payload, status=400)


def _request_correlation_id(request: Any) -> str:
    header_value = (
        request.headers.get("X-Request-Id")
        or request.headers.get("X-Correlation-Id")
        or ""
    ).strip()
    return header_value[:128] if header_value else str(uuid.uuid4())


def _request_trace_id(request: Any) -> str:
    value = (
        request.headers.get("X-Trace-Id")
        or request.headers.get("X-Request-Id")
        or request.headers.get("X-Correlation-Id")
        or ""
    ).strip()
    return value[:128] if value else str(uuid.uuid4())


def _idempotency_key(request: Any) -> str:
    value = (
        request.headers.get("Idempotency-Key")
        or request.headers.get("X-Idempotency-Key")
        or ""
    ).strip()
    return value[:256]


def _cache_key_for_submit(school_id: Any, idempotency_key: str) -> str:
    return f"admissions_submit:{school_id}:{idempotency_key}"


def _cache_increment_with_window(key: str, ttl_seconds: int) -> int:
    added = cache.add(key, 1, timeout=ttl_seconds)
    if added:
        return 1
    try:
        return int(cache.incr(key))
    except ValueError:
        cache.set(key, 1, timeout=ttl_seconds)
        return 1


def _client_ip_address(request: Any) -> str:
    forwarded = str(request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    remote = str(request.META.get("REMOTE_ADDR") or "").strip()
    return forwarded or remote or "unknown"


def _primary_guardian_email(payload: dict[str, Any]) -> str:
    family_value = payload.get("family")
    family: dict[str, Any] = cast(dict[str, Any], family_value) if isinstance(family_value, dict) else {}
    guardians_value = family.get("guardians")
    raw_guardians: list[Any] = cast(list[Any], guardians_value) if isinstance(guardians_value, list) else []
    guardians: list[dict[str, Any]] = [
        cast(dict[str, Any], guardian)
        for guardian in raw_guardians
        if isinstance(guardian, dict)
    ]
    if guardians:
        primary = next((g for g in guardians if g.get("isPrimary")), guardians[0])
        return str(primary.get("email") or "").strip().lower()
    return str(family.get("email") or "").strip().lower()


def _abuse_throttle_response(detail: str, correlation_id: str, retry_after: int) -> Response:
    response = Response(
        {
            "detail": detail,
            "message": detail,
            "code": "rate_limited",
            "retry_after_seconds": retry_after,
        },
        status=429,
    )
    response["Retry-After"] = str(retry_after)
    return _attach_correlation(response, correlation_id)


def _enforce_submit_abuse_controls(request: Any, school_id: Any, payload: dict[str, Any], correlation_id: str) -> Response | None:
    ip = _client_ip_address(request)
    ip_bucket = f"admissions_submit_rl:ip:{school_id}:{ip}"
    ip_count = _cache_increment_with_window(ip_bucket, SUBMIT_IP_RATE_WINDOW_SECONDS)
    if ip_count > SUBMIT_IP_RATE_LIMIT:
        return _abuse_throttle_response(
            "Too many admissions submissions from this network. Please retry shortly.",
            correlation_id,
            SUBMIT_IP_RATE_WINDOW_SECONDS,
        )

    email = _primary_guardian_email(payload)
    if email:
        email_bucket = f"admissions_submit_rl:email:{school_id}:{email}"
        email_count = _cache_increment_with_window(email_bucket, SUBMIT_EMAIL_RATE_WINDOW_SECONDS)
        if email_count > SUBMIT_EMAIL_RATE_LIMIT:
            return _abuse_throttle_response(
                "Too many admissions submissions for this email. Please contact admissions support.",
                correlation_id,
                SUBMIT_EMAIL_RATE_WINDOW_SECONDS,
            )

    return None


def _attach_correlation(response: Response, correlation_id: str) -> Response:
    response["X-Correlation-Id"] = correlation_id
    response["X-Request-Id"] = correlation_id
    response_data = cast(Any, getattr(response, "data", None))
    if isinstance(response_data, dict):
        cast(dict[str, Any], response_data).setdefault("correlation_id", correlation_id)
    return response


@dataclass
class AdmissionsSubmitData:
    inquiry: dict[str, Any]
    family: dict[str, Any]
    guardians: list[dict[str, Any]]
    students: list[dict[str, Any]]
    mission: dict[str, Any]
    documents: dict[str, Any]
    financial_aid_interest: dict[str, Any]
    attestations: dict[str, Any]
    application_fee: dict[str, Any]
    campus: str
    start_term: str


def _build_legacy_guardian(family: dict[str, Any]) -> dict[str, Any] | None:
    if not any(family.get(key) for key in ("guardianName", "email", "phone")):
        return None
    return {
        "relationship": "Guardian",
        "relationshipOther": "",
        "guardianName": family.get("guardianName") or "",
        "email": family.get("email") or "",
        "phone": family.get("phone") or "",
        "isPrimary": True,
    }


def _extract_guardians(family: dict[str, Any]) -> list[dict[str, Any]]:
    guardians_value = family.get("guardians")
    raw_guardians: list[Any] = cast(list[Any], guardians_value) if isinstance(guardians_value, list) else []
    guardians = [cast(dict[str, Any], guardian) for guardian in raw_guardians if isinstance(guardian, dict)]
    if guardians:
        return guardians
    legacy_guardian = _build_legacy_guardian(family)
    return [legacy_guardian] if legacy_guardian else []


def _extract_students(payload: dict[str, Any]) -> list[dict[str, Any]]:
    students_value = payload.get("students")
    if isinstance(students_value, list) and students_value:
        raw_students: list[Any] = cast(list[Any], students_value)
        return [cast(dict[str, Any], student) for student in raw_students if isinstance(student, dict)]
    legacy_student: Any = payload.get("student")
    if isinstance(legacy_student, dict):
        return [cast(dict[str, Any], legacy_student)]
    return []


def _extract_submit_data(payload: dict[str, Any]) -> AdmissionsSubmitData:
    inquiry_value = payload.get("inquiry")
    inquiry: dict[str, Any] = cast(dict[str, Any], inquiry_value) if isinstance(inquiry_value, dict) else {}
    family_value = payload.get("family")
    family: dict[str, Any] = cast(dict[str, Any], family_value) if isinstance(family_value, dict) else {}
    students = _extract_students(payload)
    guardians = _extract_guardians(family)

    mission_value = payload.get("mission")
    mission: dict[str, Any] = cast(dict[str, Any], mission_value) if isinstance(mission_value, dict) else {}
    documents_value = payload.get("documents")
    documents: dict[str, Any] = cast(dict[str, Any], documents_value) if isinstance(documents_value, dict) else {}
    financial_aid_value = payload.get("financialAidInterest")
    financial_aid_interest: dict[str, Any] = cast(dict[str, Any], financial_aid_value) if isinstance(financial_aid_value, dict) else {}
    attestations_value = payload.get("attestations")
    attestations: dict[str, Any] = cast(dict[str, Any], attestations_value) if isinstance(attestations_value, dict) else {}
    application_fee_value = payload.get("applicationFee")
    application_fee: dict[str, Any] = cast(dict[str, Any], application_fee_value) if isinstance(application_fee_value, dict) else {}
    return AdmissionsSubmitData(
        inquiry=inquiry,
        family=family,
        guardians=guardians,
        students=students,
        mission=mission,
        documents=documents,
        financial_aid_interest=financial_aid_interest,
        attestations=attestations,
        application_fee=application_fee,
        campus=str(inquiry.get("campus") or "").strip(),
        start_term=str(inquiry.get("startTerm") or "").strip(),
    )


def _validate_guardian(guardian: dict[str, Any], index: int) -> str | None:
    base = f"family.guardians[{index}]"
    if not str(guardian.get("guardianName") or "").strip():
        return f"{base}.guardianName is required"
    if not str(guardian.get("email") or "").strip():
        return f"{base}.email is required"
    if not str(guardian.get("phone") or "").strip():
        return f"{base}.phone is required"
    relationship = str(guardian.get("relationship") or "").strip()
    if not relationship:
        return f"{base}.relationship is required"
    if relationship == "Other" and not str(guardian.get("relationshipOther") or "").strip():
        return f"{base}.relationshipOther is required"
    return None


def _validate_student(student: dict[str, Any], index: int) -> str | None:
    base = f"students[{index}]"
    if not str(student.get("firstName") or "").strip():
        return f"{base}.firstName is required"
    if not str(student.get("lastName") or "").strip():
        return f"{base}.lastName is required"
    if not str(student.get("gradeApplyingFor") or "").strip():
        return f"{base}.gradeApplyingFor is required"
    current_school = str(student.get("currentSchool") or "").strip()
    if not current_school:
        return f"{base}.currentSchool is required"
    if current_school == "Other" and not str(student.get("currentSchoolOther") or "").strip():
        return f"{base}.currentSchoolOther is required"
    return None


def _validate_application_fee(data: AdmissionsSubmitData) -> str | None:
    if not _application_fee_required():
        return None
    policy_accepted = bool(data.application_fee.get("policyAccepted"))
    waiver_requested = bool(data.application_fee.get("waiverRequested"))
    if policy_accepted and waiver_requested:
        return "applicationFee.policyAccepted and applicationFee.waiverRequested cannot both be true"
    if not policy_accepted and not waiver_requested:
        return "applicationFee.policyAccepted or applicationFee.waiverRequested is required"
    return None


def _validate_submit_data(data: AdmissionsSubmitData) -> str | None:
    if not data.campus:
        return "inquiry.campus is required"
    if not data.start_term:
        return "inquiry.startTerm is required"

    if not data.guardians:
        return "family.guardians must contain at least one guardian"

    for index, guardian in enumerate(data.guardians):
        error = _validate_guardian(guardian, index)
        if error:
            return error

    if not data.students:
        return "students must contain at least one child"

    for index, student in enumerate(data.students):
        error = _validate_student(student, index)
        if error:
            return error
    return _validate_application_fee(data)


def _create_admissions_submission_records(school_id: Any, data: AdmissionsSubmitData):
    source = _normalize_source(data.inquiry.get("heardAbout"))
    primary_guardian = next(
        (guardian for guardian in data.guardians if guardian.get("isPrimary")),
        data.guardians[0],
    )
    primary_guardian_name = str(primary_guardian.get("guardianName") or "").strip()
    first_student = data.students[0]
    first_student_last = str(first_student.get("lastName") or "").strip()
    household_name = f"{first_student_last or primary_guardian_name} Family".strip()

    applications: list[Application] = []
    applicants: list[Applicant] = []

    with transaction.atomic():
        household = Household.objects.create(
            school_id=school_id,
            name=household_name,
        )

        for student in data.students:
            application = Application.objects.create(
                school_id=school_id,
                household=household,
                status="SUBMITTED",
                submitted_at=timezone.now(),
            )

            applicant_flags: dict[str, Any] = {
                "campus": data.campus,
                "start_term": data.start_term,
                "preferred_tour_window": data.inquiry.get("preferredTourWindow") or "",
                "preferred_interview_mode": data.inquiry.get("preferredInterviewMode") or "",
                "guardians": data.guardians,
                "primary_guardian": primary_guardian,
                "church_affiliation": data.family.get("churchAffiliation") or "",
                "church_affiliation_other": data.family.get("churchAffiliationOther") or "",
                "attestations": data.attestations,
                "current_school": student.get("currentSchool") or "",
                "current_school_other": student.get("currentSchoolOther") or "",
                "student_strengths": student.get("interestsAndActivities") or student.get("strengths") or "",
                "support_needs": student.get("supportNeeds") or "",
                "mission": data.mission,
                "documents": data.documents,
                "financial_aid_interest": data.financial_aid_interest,
                "application_fee": {
                    "configured_amount": str(APPLICATION_FEE_USD),
                    "currency": APPLICATION_FEE_CURRENCY,
                    "policy_accepted": bool(data.application_fee.get("policyAccepted")),
                    "waiver_requested": bool(data.application_fee.get("waiverRequested")),
                },
            }

            applicant = Applicant.objects.create(
                school_id=school_id,
                application=application,
                first_name=str(student.get("firstName") or "").strip(),
                last_name=str(student.get("lastName") or "").strip(),
                grade_applying_for=str(student.get("gradeApplyingFor") or "").strip(),
                source=source,
                flags=applicant_flags,
            )

            ApplicationEvent.objects.create(
                school_id=school_id,
                application=application,
                event_type="inquiry_created",
                payload={
                    "source": source,
                    "campus": data.campus,
                    "start_term": data.start_term,
                },
            )
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=application,
                event_type="application_started",
                payload={"via": "prospective_family_wizard_household_v2"},
            )
            ApplicationEvent.objects.create(
                school_id=school_id,
                application=application,
                event_type="application_submitted",
                payload={"via": "prospective_family_wizard_household_v2", "applicant_id": str(applicant.id)},
            )
            _safe_register_crm_submit(
                application=application,
                source=source,
                start_term=data.start_term,
                school_id=school_id,
            )
            _ensure_application_checklist_items(application, data.documents)

            applications.append(application)
            applicants.append(applicant)

    return applications, applicants


def _build_document_lifecycle(documents: dict[str, Any]) -> list[dict[str, Any]]:
    entries = [
        ("transcript", "Transcript", bool(documents.get("transcriptReady"))),
        ("recommendations", "Recommendations", bool(documents.get("recommendationsReady"))),
        ("pastor_reference", "Pastor/Church Reference", bool(documents.get("pastorReferenceReady"))),
        ("immunization", "Immunization Records", bool(documents.get("immunizationReady"))),
    ]
    return [
        {
            "key": key,
            "label": label,
            "status": "ready" if ready else "pending",
            "next_action": "Await reviewer verification" if ready else "Submit during review phase",
        }
        for key, label, ready in entries
    ]


def _checklist_status_from_documents(item_def: ChecklistRequiredItemDef, documents: dict[str, Any]) -> str:
    ready = bool((documents or {}).get(item_def["document_flag"]))
    return ChecklistItemStatus.SUBMITTED if ready else ChecklistItemStatus.MISSING


def _infer_document_quality_status(*, filename: str, content_type: str) -> tuple[str, str]:
    normalized_name = str(filename or "").strip().lower()
    normalized_type = str(content_type or "").strip().lower()
    if not normalized_name:
        return "rejected", "Missing filename metadata."
    if normalized_type.startswith("image/") and "jpeg" not in normalized_type and "jpg" not in normalized_type and "png" not in normalized_type:
        return "review", "Image format may reduce review readability."
    if normalized_name.endswith((".pdf", ".png", ".jpg", ".jpeg")):
        return "ready", "File type accepted for review."
    return "review", "File uploaded, but preferred type is PDF or clear image."


def _checklist_dependency_state(item: ApplicationChecklistItem, item_def: ChecklistRequiredItemDef) -> dict[str, Any]:
    dependencies = [str(dep) for dep in item_def["depends_on"] if dep]
    if not dependencies:
        return {
            "blocked": False,
            "depends_on": [],
            "blocking_items": [],
            "dependency_status": "ready",
        }

    checklist_items = getattr(item.application, "checklist_items", None)
    sibling_statuses: dict[str, Any] = {}
    raw_siblings: list[Any] = list(checklist_items.all()) if checklist_items is not None else []
    for sibling in raw_siblings:
        sibling_statuses[str(getattr(sibling, "item_key", ""))] = getattr(sibling, "status", None)
    blocking_items = [
        dep for dep in dependencies
        if sibling_statuses.get(dep) not in (ChecklistItemStatus.SUBMITTED, ChecklistItemStatus.UNDER_REVIEW, ChecklistItemStatus.APPROVED)
    ]
    return {
        "blocked": bool(blocking_items),
        "depends_on": dependencies,
        "blocking_items": blocking_items,
        "dependency_status": "blocked" if blocking_items else "ready",
    }


def _ensure_application_checklist_items(application: Application, documents: dict[str, Any]) -> list[ApplicationChecklistItem]:
    items: list[ApplicationChecklistItem] = []
    for item_def in CHECKLIST_REQUIRED_ITEMS:
        status = _checklist_status_from_documents(item_def, documents)
        defaults: dict[str, Any] = {
            "school_id": application.school_id,
            "title": item_def["title"],
            "office": item_def["office"],
            "is_required": True,
            "status": status,
            "submitted_at": timezone.now() if status == ChecklistItemStatus.SUBMITTED.value else None,
        }
        checklist_item, _ = ApplicationChecklistItem.objects.update_or_create(
            application=application,
            item_key=item_def["key"],
            defaults=defaults,
        )
        items.append(checklist_item)
    return items


def _checklist_summary(items: list[ApplicationChecklistItem]) -> dict[str, int | bool]:
    required_items = [item for item in items if item.is_required]
    submitted = sum(1 for item in required_items if item.status in (ChecklistItemStatus.SUBMITTED.value, ChecklistItemStatus.UNDER_REVIEW.value, ChecklistItemStatus.APPROVED.value))
    missing = sum(1 for item in required_items if item.status in (ChecklistItemStatus.MISSING.value, ChecklistItemStatus.REJECTED.value))
    return {
        "required_total": len(required_items),
        "submitted_count": submitted,
        "missing_count": missing,
        "ready_for_review": bool(len(required_items) > 0 and missing == 0),
    }


def _checklist_item_definition(item_key: str) -> ChecklistRequiredItemDef:
    return next(
        (entry for entry in CHECKLIST_REQUIRED_ITEMS if entry["key"] == item_key),
        cast(
            ChecklistRequiredItemDef,
            {
                "key": item_key,
                "title": item_key,
                "office": "",
                "owner": "",
                "due_days": 0,
                "depends_on": [],
                "parent_visible": True,
                "reminder_days": [],
                "document_flag": "",
            },
        ),
    )


def _checklist_due_at_iso(item: ApplicationChecklistItem, item_def: ChecklistRequiredItemDef) -> str | None:
    due_days = int(item_def.get("due_days") or 0)
    if due_days <= 0:
        return None
    base = item.application.submitted_at or item.application.created_at
    if not base:
        return None
    return (base + timedelta(days=due_days)).isoformat()


def _checklist_parent_status(item: ApplicationChecklistItem) -> str:
    if item.status in (ChecklistItemStatus.SUBMITTED.value, ChecklistItemStatus.UNDER_REVIEW.value):
        return "Ready for Review"
    if item.status == ChecklistItemStatus.APPROVED.value:
        return "Checklist Complete"
    return "Checklist Incomplete"


def _serialize_checklist_item(item: ApplicationChecklistItem) -> dict[str, Any]:
    item_def = _checklist_item_definition(item.item_key)
    documents_rel = getattr(item, "documents", None)
    latest_doc = documents_rel.order_by("-created_at").first() if documents_rel is not None else None
    latest_document: dict[str, Any] | None = None
    if latest_doc:
        quality_status, quality_note = _infer_document_quality_status(
            filename=latest_doc.original_filename,
            content_type=latest_doc.content_type,
        )
        latest_document = {
            "id": str(latest_doc.id),
            "original_filename": latest_doc.original_filename,
            "uploaded_at": latest_doc.created_at.isoformat() if latest_doc.created_at else None,
            "content_type": latest_doc.content_type,
            "quality_status": quality_status,
            "quality_note": quality_note,
        }

    dependency_state = _checklist_dependency_state(item, item_def)

    return {
        "id": str(item.id),
        "item_key": item.item_key,
        "title": item.title,
        "office": item.office,
        "owner": item_def.get("owner") or item.office,
        "due_at": _checklist_due_at_iso(item, item_def),
        "depends_on": dependency_state["depends_on"],
        "dependency_status": dependency_state["dependency_status"],
        "blocking_items": dependency_state["blocking_items"],
        "is_blocked": dependency_state["blocked"],
        "is_required": item.is_required,
        "status": item.status,
        "parent_status": _checklist_parent_status(item),
        "parent_visibility": bool(item_def.get("parent_visible", True)),
        "reminder_setting": {
            "enabled": True,
            "days": item_def.get("reminder_days") or [3, 7],
        },
        "notes": item.notes or "",
        "staff_only_notes": item.notes or "",
        "submitted_at": item.submitted_at.isoformat() if item.submitted_at else None,
        "completion_timestamp": item.submitted_at.isoformat() if item.submitted_at else None,
        "latest_document": latest_document,
    }


def _promote_checklist_for_demo(application: Application):
    now = timezone.now()
    ApplicationChecklistItem.objects.filter(application=application, is_required=True).update(
        status=ChecklistItemStatus.APPROVED,
        submitted_at=now,
        notes="Sandbox demo flow: package completion assumed.",
    )


def _build_submit_milestones(data: AdmissionsSubmitData) -> list[dict[str, Any]]:
    scheduling_ready = bool(data.inquiry.get("preferredTourWindow")) and bool(data.inquiry.get("preferredInterviewMode"))
    return [
        {
            "key": "submitted",
            "title": "Application Submitted",
            "target": "Completed",
            "status": "complete",
        },
        {
            "key": "coordinator_response",
            "title": "Coordinator Outreach",
            "target": REVIEW_DECISION_SLA_TEXT,
            "status": "in_progress",
        },
        {
            "key": "readiness_review",
            "title": "Readiness and Mission Review",
            "target": REVIEW_DECISION_SLA_TEXT,
            "status": "pending",
        },
        {
            "key": "decision",
            "title": "Admissions Decision",
            "target": REVIEW_DECISION_SLA_TEXT,
            "status": "pending",
        },
        {
            "key": "next_step_scheduling",
            "title": "Tour / Interview Scheduling",
            "target": ASSESSMENT_SCHEDULING_TARGET_SLA,
            "status": "in_progress" if scheduling_ready else "pending",
        },
    ]


def _build_assessment_interview_status(data: AdmissionsSubmitData) -> dict[str, Any]:
    preferred_tour_window = str(data.inquiry.get("preferredTourWindow") or "").strip()
    preferred_interview_mode = str(data.inquiry.get("preferredInterviewMode") or "").strip()
    has_preferences = bool(preferred_tour_window and preferred_interview_mode)

    if has_preferences:
        status_value = "preferences_captured"
        parent_status = "Scheduling in Progress"
        next_action = "Admissions team will confirm your tour/interview slot."
    elif ADMISSIONS_ASSESSMENT_REQUIRED:
        status_value = "required"
        parent_status = "Action Required"
        next_action = "Select preferred tour and interview options to continue admissions scheduling."
    else:
        status_value = "optional"
        parent_status = "Optional"
        next_action = "You may share preferred scheduling options now or later."

    return {
        "required": ADMISSIONS_ASSESSMENT_REQUIRED,
        "status": status_value,
        "parent_status": parent_status,
        "preferred_tour_window": preferred_tour_window,
        "preferred_interview_mode": preferred_interview_mode,
        "next_action": next_action,
        "target_sla": ASSESSMENT_SCHEDULING_TARGET_SLA,
    }


def _application_fee_status_value(fee_required: bool, waiver_requested: bool) -> str:
    if waiver_requested:
        return "waiver_requested"
    if fee_required:
        return "pending"
    return "not_required"


def _build_enrollment_continuity(data: AdmissionsSubmitData) -> dict[str, Any]:
    fee_required = _application_fee_required()
    waiver_requested = bool(data.application_fee.get("waiverRequested"))
    fee_status = _application_fee_status_value(fee_required, waiver_requested)

    fee_rows = _fee_rows_for_household(data, [])

    return {
        "phase": "admissions_to_enrollment",
        "fee_program": {
            "application_fee": _application_fee_config(),
            "financial_aid_fee": _financial_aid_fee_config(data),
            "enrollment_fee": _enrollment_fee_config(),
            "per_child_schedule": fee_rows,
        },
        "review_sla": {
            "target": "24_hours",
            "decision_due_by": _decision_deadline_iso(),
        },
        "checklist": [
            {
                "key": "application_fee",
                "title": "Application Fee",
                "status": fee_status,
                "amount": str(APPLICATION_FEE_USD),
                "currency": APPLICATION_FEE_CURRENCY,
            },
            {
                "key": "financial_aid_fee",
                "title": "Financial Aid Fee",
                "status": "pending" if _financial_aid_fee_required(data) else "not_required",
                "amount": str(FINANCIAL_AID_FEE_USD),
                "currency": APPLICATION_FEE_CURRENCY,
            },
            {
                "key": "tour_or_interview",
                "title": "Schedule Tour or Interview",
                "status": "pending",
                "recommended_window": data.inquiry.get("preferredTourWindow") or "Not specified",
            },
            {
                "key": "record_completion",
                "title": "Complete Remaining Records",
                "status": "in_progress",
                "items_ready": sum(bool(v) for v in (data.documents or {}).values()),
            },
            {
                "key": "family_partnership_conversation",
                "title": "Mission Partnership Conversation",
                "status": "pending",
                "mode": data.inquiry.get("preferredInterviewMode") or "Phone or video",
            },
            {
                "key": "enrollment_fee",
                "title": "Enrollment Fee",
                "status": "pending" if _enrollment_fee_required() else "not_required",
                "amount": str(ENROLLMENT_FEE_USD),
                "currency": APPLICATION_FEE_CURRENCY,
            },
            {
                "key": "decision_and_enrollment_next_steps",
                "title": "Decision and Enrollment Next Steps",
                "status": "pending",
            },
        ],
    }


def _build_post_admission_lifecycle(data: AdmissionsSubmitData) -> dict[str, Any]:
    return {
        "phase": "enrollment_conversion_to_retention",
        "active_stage": "enrollment_acceptance",
        "family_portal_continuity": {
            "single_journey_thread": True,
            "duplicate_form_policy": "avoid",
        },
        "stages": [
            {
                "key": "enrollment_acceptance",
                "label": "Enrollment Acceptance",
                "status": "pending",
                "owner_team": "Admissions",
                "family_next_step": "Review enrollment agreement and confirm intent to enroll.",
            },
            {
                "key": "financial_setup",
                "label": "Financial Setup",
                "status": "pending",
                "owner_team": "Finance",
                "family_next_step": "Complete tuition plan and payment method setup.",
            },
            {
                "key": "record_activation",
                "label": "Student Record Activation",
                "status": "pending",
                "owner_team": "Registrar",
                "staff_next_step": "Convert applicant to student and activate SIS-linked records.",
            },
            {
                "key": "compliance_health",
                "label": "Compliance and Health",
                "status": "pending",
                "owner_team": "Student Services",
                "family_next_step": "Complete health, emergency, and policy acknowledgements.",
            },
            {
                "key": "academic_placement",
                "label": "Academic Placement",
                "status": "pending",
                "owner_team": ACADEMIC_OFFICE,
                "staff_next_step": "Run transcript or placement review and initial scheduling inputs.",
            },
            {
                "key": "community_integration",
                "label": "Christian Community Integration",
                "status": "pending",
                "owner_team": "Family Engagement",
                "family_next_step": "Register for orientation and community welcome events.",
            },
            {
                "key": "portal_activation",
                "label": "Portal Activation",
                "status": "pending",
                "owner_team": "Operations",
                "family_next_step": "Activate parent portal and notification preferences.",
            },
            {
                "key": "retention_readiness",
                "label": "Retention Readiness",
                "status": "pending",
                "owner_team": "Leadership",
                "staff_next_step": "Monitor onboarding completion and early engagement risk signals.",
            },
        ],
        "retention_signals": {
            "onboarding_completion": "pending",
            "community_integration": "pending",
            "portal_adoption": "pending",
            "family_engagement": "pending",
        },
        "communications": {
            "email_updates": "enabled",
            "sms_updates": "enabled_when_configured",
            "cadence": [
                "submission_confirmation",
                "review_started",
                "decision_posted",
                "enrollment_contract_issued",
            ],
        },
        "context": {
            "campus": data.campus,
            "start_term": data.start_term,
        },
    }


def _build_reviewer_summary(data: AdmissionsSubmitData, applicants: list[Applicant]) -> dict[str, Any]:
    mission = data.mission or {}
    guardian_names = [
        str(g.get("guardianName") or "").strip() for g in data.guardians if str(g.get("guardianName") or "").strip()
    ]
    student_names = [f"{a.first_name} {a.last_name}".strip() for a in applicants]
    return {
        "household": {
            "guardians": guardian_names,
            "students": student_names,
            "campus": data.campus,
            "start_term": data.start_term,
        },
        "mission_alignment": {
            "covenant_partnership": bool(mission.get("covenantPartnership")),
            "discipleship_commitment": bool(mission.get("discipleshipCommitment")),
            "service_mindset": bool(mission.get("serviceMindset")),
            "family_comments": mission.get("comments") or "",
        },
    }


def _build_admissions_finance_handoff_panel(*, data: AdmissionsSubmitData, application_fee: dict[str, Any]) -> dict[str, Any]:
    aid_intent = str((data.financial_aid_interest or {}).get("intent") or "").strip().lower()
    fee_status = str(application_fee.get("status") or "unknown")
    fee_finance_state = str((application_fee.get("finance") or {}).get("state") or "unknown")
    fee_ready_states = {
        "invoiced",
        "waiver_requested",
        "not_required",
        "not_applicable",
    }
    fee_readiness = fee_finance_state in fee_ready_states or fee_status in {"waiver_requested", "not_required"}

    aid_readiness_status = "not_requested"
    if aid_intent == "applying":
        aid_readiness_status = "queued_for_aid_workspace"
    elif aid_intent in {"not_applying", "not_needed"}:
        aid_readiness_status = "not_applying"

    return {
        "status": "ready" if fee_readiness else "needs_attention",
        "next_owner": "Finance",
        "fee_readiness": {
            "status": "ready" if fee_readiness else "needs_attention",
            "application_fee_status": fee_status,
            "finance_state": fee_finance_state,
        },
        "aid_readiness": {
            "status": aid_readiness_status,
            "financial_aid_intent": aid_intent or "unspecified",
        },
        "deposit_readiness": {
            "status": "pending_acceptance",
            "required": True,
        },
    }


def _build_family_affordability_profile(
    *,
    data: AdmissionsSubmitData,
    application_ids: list[str],
    application_fee: dict[str, Any],
) -> dict[str, Any]:
    rows = cast(list[dict[str, Any]], application_fee.get("per_child_schedule") or _fee_rows_for_household(data, application_ids))

    def _sum_amount(field: str) -> str:
        total = Decimal("0.00")
        for row in rows:
            total += Decimal(str(row.get(field) or "0.00"))
        return str(total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

    aid_intent = str((data.financial_aid_interest or {}).get("intent") or "").strip().lower()
    return {
        "currency": APPLICATION_FEE_CURRENCY,
        "student_count": len(data.students),
        "aid_requested": aid_intent == "applying",
        "aid_intent": aid_intent or "unspecified",
        "upfront": {
            "application_fee_total": _sum_amount("application_fee"),
            "financial_aid_fee_total": _sum_amount("financial_aid_fee"),
            "enrollment_fee_total": _sum_amount("enrollment_fee"),
            "total_estimated": _sum_amount("total"),
        },
        "discount_policy": _application_fee_config().get("discount_policy"),
    }


def _build_application_fee_status_card(*, application_fee: dict[str, Any]) -> dict[str, Any]:
    payment_handoff = cast(dict[str, Any], application_fee.get("payment_handoff") or {})
    return {
        "status": str(application_fee.get("status") or "unknown"),
        "finance_state": str((application_fee.get("finance") or {}).get("state") or "unknown"),
        "requires_action": bool(payment_handoff.get("state") == "ready"),
        "cta": {
            "label": "Complete application fee payment",
            "endpoint": payment_handoff.get("endpoint") or PAYMENT_INTENT_ENDPOINT,
            "method": payment_handoff.get("method") or "POST",
        },
    }


def _build_application_fee_status(data: AdmissionsSubmitData) -> dict[str, Any]:
    waiver_requested = bool(data.application_fee.get("waiverRequested"))
    policy_accepted = bool(data.application_fee.get("policyAccepted"))
    fee_required = _application_fee_required()
    status = _application_fee_status_value(fee_required, waiver_requested)
    config = _application_fee_config()
    return {
        **config,
        "policy_accepted": policy_accepted,
        "waiver_requested": waiver_requested,
        "status": status,
        "due_stage": "application_submitted",
    }


def _build_payment_handoff(*, invoice_id: Any, amount_cents: int, correlation_id: str) -> dict[str, Any]:
    return {
        "state": "ready",
        "requires_auth": True,
        "endpoint": PAYMENT_INTENT_ENDPOINT,
        "method": "POST",
        "payload": {
            "invoice_id": str(invoice_id),
            "amount_cents": amount_cents,
            "currency": APPLICATION_FEE_CURRENCY,
            "idempotency_key": f"admissions-fee-intent:{invoice_id}",
        },
        "instructions": "Sign in to complete secure payment processing in the finance module.",
        "correlation_id": correlation_id,
    }


def _build_next_step_orchestration(*, checklist_items: list[ApplicationChecklistItem], demo_completed: bool) -> dict[str, Any]:
    summary = _checklist_summary(checklist_items)
    docs_complete = summary["missing_count"] == 0
    package_complete = docs_complete or demo_completed

    return {
        "family_communications": {
            "email_contacted": package_complete,
            "sms_contacted": package_complete,
            "status": "complete" if package_complete else "pending",
            "cadence": [
                "submission_confirmation",
                "document_missing_reminders",
                "review_started",
                "decision_posted",
                "enrollment_contract_issued",
            ],
        },
        "records_package": {
            "required_files_received": summary["submitted_count"],
            "required_files_total": summary["required_total"],
            "status": "complete" if package_complete else "in_progress",
        },
        "contract": {
            "status": "ready_for_esign" if package_complete else "awaiting_records_package",
            "sample_contract_template_available": True,
            "e_sign": {
                "provider": "sample",
                "school_copy_delivery": "automatic",
                "family_copy_delivery": "automatic",
            },
        },
        "financial_aid": {
            "kickoff_trigger": "contract_signed",
            "status": "ready_after_contract" if package_complete else "blocked_until_contract_ready",
            "next_step": "Family completes financial aid application immediately after contract signature.",
        },
    }


def _resolve_finance_payer_user(*, school: Any, guardians: list[dict[str, Any]]):
    primary = next((g for g in guardians if g.get("isPrimary")), guardians[0] if guardians else {})
    email = str(primary.get("email") or "").strip().lower()
    if not email:
        return None

    user_model = get_user_model()
    payer = user_model.objects.filter(school=school, email__iexact=email).first()
    if payer:
        return payer

    # Use deterministic username seed plus suffix to avoid global username collisions.
    seed = email.split("@", 1)[0] or "guardian"
    username = f"{seed}-{uuid.uuid4().hex[:8]}"
    payer = user_model.objects.create(
        school=school,
        username=username,
        email=email,
        first_name=str(primary.get("guardianName") or "").strip()[:150],
        is_active=True,
    )
    payer.set_unusable_password()
    payer.save(update_fields=["password"])
    return payer


def _create_application_fee_finance_records(*, school: Any, data: AdmissionsSubmitData, application_ids: list[str], correlation_id: str) -> dict[str, Any]:
    fee_status = _build_application_fee_status(data)
    if not fee_status["required"]:
        fee_status["finance"] = {"state": "not_applicable"}
        return fee_status

    if fee_status["waiver_requested"]:
        fee_status["finance"] = {"state": "waiver_requested"}
        return fee_status

    payer = _resolve_finance_payer_user(school=school, guardians=data.guardians)
    if payer is None:
        fee_status["finance"] = {
            "state": "payer_unresolved",
            "message": "Guardian email required to generate finance invoice.",
        }
        return fee_status

    try:
        from finance.models import FinanceObligation, ObligationType
        from finance.services import create_invoice_from_obligations
    except Exception:
        fee_status["finance"] = {
            "state": "finance_module_unavailable",
            "message": "Finance module unavailable; admissions submission retained.",
        }
        return fee_status

    obligations = []
    obligation_rows = []
    amount_cents_total = 0
    for child_index, app_id in enumerate(application_ids or [str(uuid.uuid4())], start=1):
        discounted_fee = _apply_child_discount(APPLICATION_FEE_USD, child_index)
        fee_cents = int((discounted_fee * 100).quantize(Decimal("1")))
        amount_cents_total += fee_cents
        reference = f"admissions_fee:{app_id}"
        obligation = FinanceObligation.objects.filter(
            school=school,
            payer_user=payer,
            obligation_type=ObligationType.FEE,
            reference=reference,
        ).first()

        if obligation is None:
            obligation = FinanceObligation.objects.create(
                school=school,
                payer_user=payer,
                obligation_type=ObligationType.FEE,
                description=f"Admissions Application Fee (Child {child_index})",
                due_date=timezone.localdate(),
                amount_cents=fee_cents,
                currency=APPLICATION_FEE_CURRENCY,
                reference=reference,
                academic_year_label=data.start_term,
            )
        else:
            obligation.amount_cents = fee_cents
            obligation.save(update_fields=["amount_cents", "updated_at"])

        obligations.append(obligation)
        obligation_rows.append(
            {
                "child_index": child_index,
                "application_id": app_id,
                "discount_percent": _child_discount_percent(child_index),
                "amount": str(discounted_fee),
                "obligation_id": obligation.id,
            }
        )

    invoice = create_invoice_from_obligations(
        school=school,
        payer_user=payer,
        period_start=timezone.localdate(),
        period_end=timezone.localdate(),
        due_date=timezone.localdate(),
        obligations=obligations,
        created_by=None,
    )

    fee_status["finance"] = {
        "state": "invoiced",
        "payer_user_id": str(payer.id),
        "obligation_ids": [row["obligation_id"] for row in obligation_rows],
        "per_child_obligations": obligation_rows,
        "invoice_id": invoice.id,
        "collection_path": PAYMENT_INTENT_ENDPOINT,
    }
    fee_status["per_child_schedule"] = _fee_rows_for_household(data, application_ids)
    fee_status["payment_handoff"] = _build_payment_handoff(
        invoice_id=invoice.id,
        amount_cents=amount_cents_total,
        correlation_id=correlation_id,
    )
    return fee_status


def _d2(x: Decimal) -> str:
    """Decimal to string with exactly 2 decimals."""
    return str(x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _rate(numer: int, denom: int) -> str:
    if denom <= 0:
        return "0.00"
    return _d2(Decimal(numer) / Decimal(denom))


def _normalize_ay_name(name: str) -> str:
    """Normalize academic year name: en-dash (–) and em-dash (—) to hyphen (-)."""
    return (name or "").strip().replace("\u2013", "-").replace("\u2014", "-")


def _find_academic_year_by_name(qs, academic_year: str):
    ay_norm = _normalize_ay_name(academic_year)
    exact = qs.filter(name=academic_year).first()
    if exact:
        return exact
    for candidate in qs:
        if _normalize_ay_name(candidate.name) == ay_norm:
            return candidate
    return None


def _get_academic_year_window(school_id: str, academic_year: str | None):
    """
    Returns: (academic_year_name, start_date, end_date, is_explicit)
    If academic_year is None, use current AcademicYear for the school.
    is_explicit: True if academic_year param was provided (indicates date filtering should apply).
    """
    qs = AcademicYear.objects.filter(school_id=school_id)
    is_explicit = academic_year is not None

    ay = _find_academic_year_by_name(qs, academic_year) if academic_year else None
    if ay is None and not academic_year:
        ay = qs.filter(is_current=True).first() or qs.order_by("-start_date").first()

    if not ay:
        # No AY configured: treat as unbounded
        return (academic_year or "unknown", None, None, is_explicit)

    return (ay.name, ay.start_date, ay.end_date, is_explicit)


def _compute_stage(
    app: Application,
    has_inquiry: bool,
    has_tour_scheduled: bool,
    has_tour_completed: bool,
    decision: str | None,
    enrolled: bool,
) -> str:
    """Deterministically compute stage from Application status + events."""
    # Highest precedence: enrolled
    if enrolled:
        return "enrolled"

    # Decisions (from events)
    if decision == "accepted":
        return "accepted"
    if decision == "waitlisted":
        return "waitlisted"
    if decision == "declined":
        return "declined"

    # Review/submission
    if app.status == "IN_REVIEW":
        return "in_review"
    if app.status == "SUBMITTED":
        return "application_submitted"
    if app.status == "DRAFT":
        # If inquiry exists, show earlier funnel stage if available
        if has_tour_completed:
            return "tour_completed"
        if has_tour_scheduled:
            return "tour_scheduled"
        if has_inquiry:
            return "inquiry"
        return "application_started"
    if app.status == "DECIDED":
        # If DECIDED but no decision event exists, treat as declined (strictness avoids "mystery accepted").
        return "declined"

    return "application_started"


def _decision_from_payload(payload: dict) -> str | None:
    """Extract decision from ApplicationEvent payload."""
    d = (payload or {}).get("decision")
    if d in ("accepted", "waitlisted", "declined"):
        return d
    return None


def _default_enrollment_state_for_application(app: Application) -> dict[str, Any]:
    if not _application_is_post_acceptance(app):
        return {
            "contract_status": CONTRACT_NOT_APPLICABLE,
            "deposit_status": DEPOSIT_NOT_APPLICABLE,
        }
    return {
        "contract_status": CONTRACT_NOT_STARTED,
        "deposit_status": DEPOSIT_PENDING,
    }


def _application_is_post_acceptance(app: Application) -> bool:
    if ApplicationEvent.objects.filter(
        school_id=app.school_id,
        application_id=app.id,
        event_type="enrollment_confirmed",
    ).exists():
        return True

    accepted = ApplicationEvent.objects.filter(
        school_id=app.school_id,
        application_id=app.id,
        event_type="decision_made",
        payload__decision="accepted",
    ).exists()
    return bool(accepted)


def _aid_sync_state_for_application(app: Application) -> dict[str, Any]:
    default = {
        "aid_award_status": "not_recorded",
        "aid_contract_sync_status": "not_applicable",
        "aid_billing_sync_status": "not_applicable",
        "aid_award_count": 0,
    }
    household_id = getattr(app, "household_id", None)
    if not household_id:
        return default

    award_summary = build_award_summary_by_household(school_id=app.school_id, household_ids=[household_id]).get(
        household_id,
        {"count": 0},
    )
    award_count = int(award_summary.get("count") or 0)
    if award_count <= 0:
        return default

    if _application_is_post_acceptance(app):
        contract_sync = "ready_for_contract_adjustment"
        billing_sync = "ready_for_billing_application"
    else:
        contract_sync = "pending_acceptance"
        billing_sync = "pending_acceptance"

    return {
        "aid_award_status": "award_recorded",
        "aid_contract_sync_status": contract_sync,
        "aid_billing_sync_status": billing_sync,
        "aid_award_count": award_count,
    }


def _latest_enrollment_state_for_application(app: Application) -> dict[str, Any]:
    aid_sync = _aid_sync_state_for_application(app)
    lifecycle_chain = _lifecycle_chain_state_for_application(app)
    baseline = _default_enrollment_state_for_application(app)
    latest = (
        ApplicationEvent.objects.filter(
            school_id=app.school_id,
            application_id=app.id,
            event_type=ENROLLMENT_STATE_EVENT_TYPE,
        )
        .order_by("-created_at")
        .first()
    )

    state = {**baseline, **aid_sync, **lifecycle_chain}
    if latest is None or not isinstance(latest.payload, dict):
        return state

    payload = cast(dict[str, Any], latest.payload)
    state.update(
        {
            "contract_status": str(payload.get("contract_status") or state["contract_status"]),
            "deposit_status": str(payload.get("deposit_status") or state["deposit_status"]),
            "note": str(payload.get("note") or ""),
            "transition_reason": str(payload.get("transition_reason") or ""),
            "owner_assignment": str(payload.get("owner_assignment") or ""),
            "trace_id": str(payload.get("trace_id") or ""),
        }
    )
    return state


def _lifecycle_chain_state_for_application(app: Application) -> dict[str, Any]:
    enrolled = ApplicationEvent.objects.filter(
        school_id=app.school_id,
        application_id=app.id,
        event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
    ).exists()
    classroom_ready = ApplicationEvent.objects.filter(
        school_id=app.school_id,
        application_id=app.id,
        event_type__in=[CLASSROOM_READINESS_EVENT_TYPE, "classroom_ready"],
    ).exists()
    portal_active = ApplicationEvent.objects.filter(
        school_id=app.school_id,
        application_id=app.id,
        event_type__in=[PARENT_PORTAL_ACTIVATED_EVENT_TYPE, "portal_activated"],
    ).exists()

    post_acceptance = _application_is_post_acceptance(app)
    if enrolled:
        applicant_to_student = "completed"
    elif post_acceptance:
        applicant_to_student = "ready"
    else:
        applicant_to_student = "pending"

    if classroom_ready:
        readiness = "completed"
    elif enrolled:
        readiness = "in_progress"
    else:
        readiness = "pending"

    if portal_active:
        portal = "completed"
    elif enrolled:
        portal = "in_progress"
    else:
        portal = "pending"

    return {
        "applicant_to_student_status": applicant_to_student,
        "classroom_readiness_status": readiness,
        "parent_portal_activation_status": portal,
    }


def _validate_state_transition(*, current: str, requested: str, graph: dict[str, set[str]], state_name: str):
    if requested == current:
        return None
    allowed = graph.get(current, set())
    if requested in allowed:
        return None
    return f"Invalid {state_name} transition: {current} -> {requested}. Allowed: {sorted(allowed)}"


def _application_has_event(app: Application, event_type: str) -> bool:
    return ApplicationEvent.objects.filter(
        school_id=app.school_id,
        application_id=app.id,
        event_type=event_type,
    ).exists()


def _resolve_legacy_academic_year(*, school) -> AcademicYear | None:
    return (
        AcademicYear.objects.filter(school=school)
        .order_by("-is_current", "start_date")
        .first()
    )


def _resolve_or_create_legacy_family(*, school, household):
    from core.models import Family, HouseholdFamilyLink

    if household is None:
        return None

    link = HouseholdFamilyLink.objects.filter(school=school, household_id=household.id).select_related("family").first()
    if link is not None:
        return link.family

    base_name = str(getattr(household, "name", "") or "Admissions Family").strip() or "Admissions Family"
    family_name = base_name
    suffix = 1
    while Family.objects.filter(school=school, family_name=family_name).exists():
        family_name = f"{base_name} {suffix}"
        suffix += 1

    family = Family.objects.create(school=school, family_name=family_name)
    HouseholdFamilyLink.objects.create(
        school=school,
        household_id=household.id,
        family=family,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    )
    return family


def _resolve_legacy_grade_level(*, school, grade_code: str):
    if not grade_code:
        return None
    from core.models import GradeLevel

    normalized = str(grade_code).strip().upper()
    if normalized == "PK":
        normalized = "PK"
    return GradeLevel.objects.filter(school=school, code=normalized).first()


def _resolve_or_create_legacy_student(*, school, family, applicant: Applicant, ordinal: int):
    from core.models import Student as CoreStudent

    if family is None:
        return None

    existing = CoreStudent.objects.filter(
        school=school,
        family=family,
        first_name__iexact=applicant.first_name,
        last_name__iexact=applicant.last_name,
    ).first()
    if existing is not None:
        return existing

    student_number = f"APP-{str(applicant.application_id).replace('-', '')[:6]}-{ordinal + 1:02d}"
    grade_level = _resolve_legacy_grade_level(school=school, grade_code=applicant.grade_applying_for)
    return CoreStudent.objects.create(
        school=school,
        family=family,
        student_number=student_number,
        first_name=applicant.first_name,
        last_name=applicant.last_name,
        dob=applicant.dob or timezone.localdate(),
        status="ACTIVE",
        current_grade_level=grade_level,
    )


def _sync_legacy_admissions_application(*, app: Application, academic_year, family, applicant: Applicant, ordinal: int, target_status: str):
    from admissions.models import AdmissionsApplication

    legacy_student = _resolve_or_create_legacy_student(
        school=academic_year.school,
        family=family,
        applicant=applicant,
        ordinal=ordinal,
    )
    legacy_app, _ = AdmissionsApplication.objects.get_or_create(
        school=academic_year.school,
        academic_year=academic_year,
        family=family,
        student=legacy_student,
        defaults={
            "status": target_status,
            "submitted_at": app.submitted_at,
            "notes_internal": f"canonical_application_id={app.id}",
        },
    )
    update_fields = []
    if legacy_app.status != target_status:
        legacy_app.status = target_status
        update_fields.append("status")
    if legacy_app.submitted_at is None and app.submitted_at is not None:
        legacy_app.submitted_at = app.submitted_at
        update_fields.append("submitted_at")
    if f"canonical_application_id={app.id}" not in str(legacy_app.notes_internal or ""):
        legacy_app.notes_internal = f"{legacy_app.notes_internal}\ncanonical_application_id={app.id}".strip()
        update_fields.append("notes_internal")
    if update_fields:
        legacy_app.save(update_fields=update_fields + ["updated_at"])
    return str(legacy_app.id)


def _create_legacy_conversion_session(*, school, actor_user, academic_year, application_ids: list[str], target_status: str):
    from admissions.models import AdmissionsApplication
    from enrollment_conversion_wizard.models import EnrollmentConversionWizardSession

    if not application_ids:
        return None
    if target_status != AdmissionsApplication.STATUS_ENROLLED:
        return None

    session = EnrollmentConversionWizardSession.objects.create(
        school=school,
        created_by=actor_user if getattr(actor_user, "is_authenticated", False) else None,
        academic_year_label=academic_year.name,
        from_status=AdmissionsApplication.STATUS_ACCEPTED,
        application_ids=application_ids,
        commit_result={"converted": len(application_ids)},
        status=EnrollmentConversionWizardSession.STATUS_VERIFIED,
    )
    return {"session_id": str(session.id), "status": session.status}


def _upsert_legacy_admissions_applications(*, app: Application, actor_user, target_status: str):
    try:
        from admissions.models import AdmissionsApplication
    except Exception:
        return {"state": "legacy_admissions_unavailable", "count": 0}

    school = School.objects.filter(id=app.school_id).first()
    household = getattr(app, "household", None)
    if school is None or household is None:
        return {"state": "legacy_bridge_unavailable", "count": 0}

    academic_year = _resolve_legacy_academic_year(school=school)
    family = _resolve_or_create_legacy_family(school=school, household=household)
    if academic_year is None or family is None:
        return {"state": "legacy_bridge_unavailable", "count": 0}

    synced_ids = [
        _sync_legacy_admissions_application(
            app=app,
            academic_year=academic_year,
            family=family,
            applicant=applicant,
            ordinal=ordinal,
            target_status=target_status,
        )
        for ordinal, applicant in enumerate(app.applicants.order_by("created_at", "id"))
    ]

    session_state = None
    if target_status == AdmissionsApplication.STATUS_ENROLLED and synced_ids:
        session_state = _create_legacy_conversion_session(
            school=school,
            actor_user=actor_user,
            academic_year=academic_year,
            application_ids=synced_ids,
            target_status=target_status,
        )

    return {
        "state": target_status.lower(),
        "count": len(synced_ids),
        "application_ids": synced_ids,
        "conversion_session": session_state,
    }


def _lifecycle_chain_request_flags(request_payload: dict) -> tuple[bool, bool, bool]:
    return (
        bool(request_payload.get("mark_enrollment_confirmed")),
        bool(request_payload.get("mark_classroom_ready")),
        bool(request_payload.get("mark_parent_portal_activated")),
    )


def _validate_lifecycle_chain_request(*, app: Application, state: dict, requested_enrollment: bool, requested_classroom_ready: bool, requested_portal_activation: bool):
    enrollment_confirmed = _application_has_event(app, ENROLLMENT_CONFIRMED_EVENT_TYPE)
    if requested_enrollment and not enrollment_confirmed:
        if state.get("contract_status") != CONTRACT_COUNTERSIGNED or state.get("deposit_status") not in (DEPOSIT_PAID, DEPOSIT_WAIVED):
            return Response(
                {
                    "detail": "Enrollment confirmation requires countersigned contract and paid or waived deposit.",
                    "contract_status": state.get("contract_status"),
                    "deposit_status": state.get("deposit_status"),
                },
                status=409,
            )

    enrollment_available = enrollment_confirmed or requested_enrollment
    if requested_classroom_ready and not enrollment_available:
        return Response(
            {"detail": "Classroom readiness can be completed only after enrollment confirmation."},
            status=409,
        )
    if requested_portal_activation and not enrollment_available:
        return Response(
            {"detail": "Parent portal activation can be completed only after enrollment confirmation."},
            status=409,
        )
    return None


def _create_lifecycle_event_if_missing(*, app: Application, event_type: str, updated_by: str, note: str, created_events: list[str]):
    if _application_has_event(app, event_type):
        return
    ApplicationEvent.objects.create(
        school_id=app.school_id,
        application=app,
        event_type=event_type,
        payload={"note": note, "updated_by": updated_by},
    )
    created_events.append(event_type)


def _apply_lifecycle_chain_updates(*, app: Application, actor_user, note: str, request_payload: dict):
    requested_enrollment, requested_classroom_ready, requested_portal_activation = _lifecycle_chain_request_flags(request_payload)

    if not any([requested_enrollment, requested_classroom_ready, requested_portal_activation]):
        return None, None

    state = _latest_enrollment_state_for_application(app)
    error = _validate_lifecycle_chain_request(
        app=app,
        state=state,
        requested_enrollment=requested_enrollment,
        requested_classroom_ready=requested_classroom_ready,
        requested_portal_activation=requested_portal_activation,
    )
    if error is not None:
        return None, error

    created_events = []
    updated_by = str(getattr(actor_user, "email", "") or getattr(actor_user, "username", ""))

    if requested_enrollment:
        _create_lifecycle_event_if_missing(
            app=app,
            event_type=ENROLLMENT_CONFIRMED_EVENT_TYPE,
            updated_by=updated_by,
            note=note,
            created_events=created_events,
        )

    if requested_classroom_ready:
        _create_lifecycle_event_if_missing(
            app=app,
            event_type=CLASSROOM_READINESS_EVENT_TYPE,
            updated_by=updated_by,
            note=note,
            created_events=created_events,
        )

    if requested_portal_activation:
        _create_lifecycle_event_if_missing(
            app=app,
            event_type=PARENT_PORTAL_ACTIVATED_EVENT_TYPE,
            updated_by=updated_by,
            note=note,
            created_events=created_events,
        )

    return created_events, None


def _safe_register_crm_submit(*, application: Application, source: str, start_term: str, school_id):
    # CRM is an add-on surface; admissions remains canonical even if CRM hook fails.
    try:
        from crm_marketing.services import register_admissions_submit

        register_admissions_submit(
            application,
            source=source,
            start_term=start_term,
        )
    except Exception:
        logger.exception(
            "crm_marketing_register_submit_failed",
            extra={"application_id": str(application.id), "school_id": str(school_id)},
        )


def _crm_stage_for_enrollment_state(contract_status: str, deposit_status: str) -> str:
    from crm_marketing.models import LeadStage

    if contract_status == CONTRACT_COUNTERSIGNED and deposit_status in (DEPOSIT_PAID, DEPOSIT_WAIVED):
        return LeadStage.ENROLLED
    return LeadStage.ACCEPTED


def _safe_register_crm_workflow_update(*, app: Application, contract_status: str, deposit_status: str, user, school_id):
    try:
        from crm_marketing.services import register_workflow_update

        register_workflow_update(
            app,
            stage=_crm_stage_for_enrollment_state(contract_status, deposit_status),
            summary="Admissions enrollment contract/deposit state updated",
            payload={
                "contract_status": contract_status,
                "deposit_status": deposit_status,
            },
            created_by=user,
        )
    except Exception:
        logger.exception(
            "crm_marketing_register_workflow_update_failed",
            extra={"application_id": str(app.id), "school_id": str(school_id)},
        )


def _normalize_contract_line_items(raw_items: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    normalized = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or item.get("name") or "").strip()
        category = str(item.get("category") or "other").strip().lower()
        amount_value: Any = item.get("amount_cents")
        try:
            amount_cents = int(amount_value or 0)
        except (TypeError, ValueError):
            continue
        if not label:
            continue
        normalized.append(
            {
                "label": label[:120],
                "category": category[:48],
                "amount_cents": amount_cents,
                "meta": item.get("meta") if isinstance(item.get("meta"), dict) else {},
            }
        )
    return normalized


def _compute_contract_totals(line_items: list[dict[str, Any]], totals_payload: Any) -> dict[str, int]:
    computed: dict[str, int] = cast(dict[str, int], dict.fromkeys(CONTRACT_TOTAL_KEYS, 0))
    category_to_total = {
        "tuition": "gross_tuition_cents",
        "fee": "fees_cents",
        "fees": "fees_cents",
        "discount": "discounts_cents",
        "aid": "aid_cents",
        "scholarship": "scholarships_cents",
        "esa": "esa_voucher_tax_credit_cents",
        "voucher": "esa_voucher_tax_credit_cents",
        "tax_credit": "esa_voucher_tax_credit_cents",
        "donor": "donor_assistance_cents",
        "deposit": "deposit_cents",
        "due_today": "amount_due_today_cents",
    }

    for item in line_items:
        field = category_to_total.get(str(item.get("category") or "").strip().lower())
        if not field:
            continue
        amount_value: Any = item.get("amount_cents")
        computed[field] += int(amount_value or 0)

    declared = totals_payload if isinstance(totals_payload, dict) else {}
    for key in CONTRACT_TOTAL_KEYS:
        if key in declared:
            try:
                computed[key] = int(declared.get(key) or 0)
            except (TypeError, ValueError):
                continue

    if computed["amount_due_today_cents"] == 0:
        computed["amount_due_today_cents"] = max(0, computed["deposit_cents"])

    computed["net_family_obligation_cents"] = (
        computed["gross_tuition_cents"]
        + computed["fees_cents"]
        - computed["discounts_cents"]
        - computed["aid_cents"]
        - computed["scholarships_cents"]
        - computed["esa_voucher_tax_credit_cents"]
        - computed["donor_assistance_cents"]
        - computed["deposit_cents"]
    )
    return computed


def _latest_contract_for_application(app: Application):
    return (
        EnrollmentContract.objects.filter(school_id=app.school_id, application=app)
        .order_by("-version", "-created_at")
        .first()
    )


def _serialize_enrollment_contract(contract: EnrollmentContract) -> dict[str, Any]:
    totals = contract.contract_totals if isinstance(contract.contract_totals, dict) else {}
    return {
        "contract_id": str(contract.id),
        "application_id": str(contract.application_id),
        "version": contract.version,
        "status": contract.status,
        "line_items": contract.line_items or [],
        "totals": {key: int(totals.get(key) or 0) for key in CONTRACT_TOTAL_KEYS},
        "payment_plan": contract.payment_plan,
        "payment_schedule": contract.payment_schedule,
        "responsible_payer": contract.responsible_payer,
        "refund_terms": contract.refund_terms,
        "note": contract.note,
        "amended_from": str(contract.amended_from_id) if contract.amended_from_id else None,
        "issued_at": contract.issued_at.isoformat() if contract.issued_at else None,
        "signed_at": contract.signed_at.isoformat() if contract.signed_at else None,
        "countersigned_at": contract.countersigned_at.isoformat() if contract.countersigned_at else None,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
        "m365_handoff": _build_contract_m365_handoff(application_ids=[str(contract.application_id)]),
    }


def _resolve_contract_payer_user(*, app: Application, fallback_user=None):
    user_model = get_user_model()
    household = getattr(app, "household", None)
    if household is not None:
        guardian = household.guardians.order_by("-is_primary", "created_at").first()
        guardian_email = str(getattr(guardian, "email", "") or "").strip().lower()
        if guardian_email:
            payer = user_model.objects.filter(email__iexact=guardian_email).first()
            if payer:
                return payer
    return fallback_user


def _ensure_billing_obligation_for_countersigned_contract(*, school, app: Application, contract: EnrollmentContract, actor_user):
    if contract.status != EnrollmentContractStatus.COUNTERSIGNED.value:
        return {"state": "not_applicable"}

    payer_user = _resolve_contract_payer_user(app=app, fallback_user=actor_user)
    if payer_user is None:
        return {"state": "payer_unresolved"}

    net_amount = int((contract.contract_totals or {}).get("net_family_obligation_cents") or 0)
    amount_cents = max(0, net_amount)

    try:
        from finance.models import FinanceObligation, ObligationType
        from finance.services import create_invoice_from_obligations
    except Exception:
        return {"state": "finance_module_unavailable"}

    reference = f"enrollment_contract:{app.id}:v{contract.version}"
    obligation, created = FinanceObligation.objects.get_or_create(
        school=school,
        payer_user=payer_user,
        obligation_type=ObligationType.TUITION,
        reference=reference,
        defaults={
            "description": f"Enrollment Contract v{contract.version}",
            "due_date": timezone.localdate(),
            "amount_cents": amount_cents,
            "currency": contract.currency,
            "academic_year_label": "",
            "created_by": actor_user,
            "updated_by": actor_user,
        },
    )

    if not created:
        obligation.amount_cents = amount_cents
        obligation.currency = contract.currency
        obligation.updated_by = actor_user
        obligation.save(update_fields=["amount_cents", "currency", "updated_by", "updated_at"])

    invoice = create_invoice_from_obligations(
        school=school,
        payer_user=payer_user,
        period_start=timezone.localdate(),
        period_end=timezone.localdate(),
        due_date=timezone.localdate(),
        obligations=[obligation],
        created_by=actor_user,
    )

    return {
        "state": "billing_obligation_created",
        "obligation_id": obligation.id,
        "invoice_id": invoice.id,
        "reference": reference,
    }


def _contract_status_from_enrollment_state(contract_status: str) -> str:
    return CONTRACT_RECORD_STATUS_MAP.get(contract_status, EnrollmentContractStatus.DRAFT)


def _resolve_requested_contract_status(*, latest: EnrollmentContract | None, payload: dict[str, Any], status_hint: str | None):
    requested_status = str(payload.get("status") or "").strip().lower()
    if requested_status in EnrollmentContractStatus.values:
        return requested_status
    if status_hint:
        return status_hint
    if latest is not None:
        return latest.status
    return EnrollmentContractStatus.DRAFT


def _stamp_contract_status_timestamps(contract: EnrollmentContract):
    if contract.status == EnrollmentContractStatus.ISSUED.value and contract.issued_at is None:
        contract.issued_at = timezone.now()
    if contract.status == EnrollmentContractStatus.SIGNED.value and contract.signed_at is None:
        contract.signed_at = timezone.now()
    if contract.status == EnrollmentContractStatus.COUNTERSIGNED.value and contract.countersigned_at is None:
        contract.countersigned_at = timezone.now()


def _create_contract_for_application(*, app: Application, actor_user, payload: dict[str, Any], status: str, line_items: list[dict[str, Any]], totals: dict[str, Any]):
    contract = EnrollmentContract.objects.create(
        school_id=app.school_id,
        application=app,
        version=1,
        status=status,
        line_items=line_items,
        contract_totals=totals,
        net_amount_cents=totals.get("net_family_obligation_cents", 0),
        payment_plan=str(payload.get("payment_plan") or "")[:80],
        payment_schedule=str(payload.get("payment_schedule") or "")[:255],
        responsible_payer=str(payload.get("responsible_payer") or "")[:255],
        refund_terms=str(payload.get("refund_terms") or "")[:2000],
        note=str(payload.get("note") or "")[:2000],
        created_by=str(getattr(actor_user, "email", "") or getattr(actor_user, "username", ""))[:255],
    )
    _stamp_contract_status_timestamps(contract)
    contract.save(update_fields=["issued_at", "signed_at", "countersigned_at", "updated_at"])
    return contract


def _update_contract_for_application(*, latest: EnrollmentContract, payload: dict[str, Any], status: str, line_items: list[dict[str, Any]], totals: dict[str, Any]):
    latest.status = status
    latest.line_items = line_items or latest.line_items
    latest.contract_totals = totals if line_items else latest.contract_totals
    latest.net_amount_cents = int((latest.contract_totals or {}).get("net_family_obligation_cents") or 0)
    latest.payment_plan = str(payload.get("payment_plan") or latest.payment_plan or "")[:80]
    latest.payment_schedule = str(payload.get("payment_schedule") or latest.payment_schedule or "")[:255]
    latest.responsible_payer = str(payload.get("responsible_payer") or latest.responsible_payer or "")[:255]
    latest.refund_terms = str(payload.get("refund_terms") or latest.refund_terms or "")[:2000]
    latest.note = str(payload.get("note") or latest.note or "")[:2000]
    _stamp_contract_status_timestamps(latest)
    latest.save(
        update_fields=[
            "status",
            "line_items",
            "contract_totals",
            "net_amount_cents",
            "payment_plan",
            "payment_schedule",
            "responsible_payer",
            "refund_terms",
            "note",
            "issued_at",
            "signed_at",
            "countersigned_at",
            "updated_at",
        ]
    )
    return latest


def _upsert_contract_for_application(*, app: Application, actor_user, payload: dict[str, Any], status_hint: str | None = None):
    latest = _latest_contract_for_application(app)
    line_items = _normalize_contract_line_items(payload.get("line_items"))
    totals = _compute_contract_totals(line_items, payload.get("totals"))
    requested_status = _resolve_requested_contract_status(latest=latest, payload=payload, status_hint=status_hint)

    if latest is None:
        return _create_contract_for_application(
            app=app,
            actor_user=actor_user,
            payload=payload,
            status=requested_status,
            line_items=line_items,
            totals=totals,
        )

    return _update_contract_for_application(
        latest=latest,
        payload=payload,
        status=requested_status,
        line_items=line_items,
        totals=totals,
    )


def _collect_stage_facts(events):
    decision_by_app = {}
    for row in events.filter(event_type="decision_made").values("application_id", "payload"):
        decision = _decision_from_payload(row.get("payload") or {})
        if decision:
            decision_by_app[row["application_id"]] = decision

    return {
        "inquiry": set(events.filter(event_type="inquiry_created").values_list("application_id", flat=True)),
        "tour_scheduled": set(events.filter(event_type="tour_scheduled").values_list("application_id", flat=True)),
        "tour_completed": set(events.filter(event_type="tour_completed").values_list("application_id", flat=True)),
        "enrolled": set(events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True)),
        "decision": decision_by_app,
    }


def _build_stage_counts(apps: Any, stage_facts: dict[str, Any]) -> dict[str, Any]:
    stage_counts = dict.fromkeys(STAGES, 0)
    for app in apps:
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in stage_facts["inquiry"]),
            has_tour_scheduled=(app.id in stage_facts["tour_scheduled"]),
            has_tour_completed=(app.id in stage_facts["tour_completed"]),
            decision=stage_facts["decision"].get(app.id),
            enrolled=(app.id in stage_facts["enrolled"]),
        )
        stage_counts[stage] += 1
    return stage_counts


def _build_conversion_rates(stage_counts: dict[str, Any]) -> dict[str, Any]:
    inquiry = stage_counts["inquiry"]
    submitted = stage_counts["application_submitted"]
    accepted = stage_counts["accepted"]
    enrolled = stage_counts["enrolled"]
    return {
        "inquiry_to_submitted": _rate(submitted, inquiry),
        "submitted_to_accepted": _rate(accepted, submitted),
        "accepted_to_enrolled": _rate(enrolled, accepted),
    }


def _avg_days_between(events, start_type: str, end_type: str) -> str:
    start_times = dict(
        events.filter(event_type=start_type)
        .values("application_id")
        .annotate(t=Min("created_at"))
        .values_list("application_id", "t")
    )
    end_times = dict(
        events.filter(event_type=end_type)
        .values("application_id")
        .annotate(t=Min("created_at"))
        .values_list("application_id", "t")
    )
    deltas = [
        (end_times[app_id] - start_time).days + (end_times[app_id] - start_time).seconds / 86400.0
        for app_id, start_time in start_times.items()
        if app_id in end_times and end_times[app_id] and start_time and end_times[app_id] >= start_time
    ]
    if not deltas:
        return "0.00"
    return _d2(Decimal(sum(deltas)) / Decimal(len(deltas)))


def _build_velocity(events: Any) -> dict[str, Any]:
    return {
        "inquiry_to_tour_completed_avg": _avg_days_between(events, "inquiry_created", "tour_completed"),
        "tour_completed_to_submitted_avg": _avg_days_between(events, "tour_completed", "application_submitted"),
        "submitted_to_decision_avg": _avg_days_between(events, "application_submitted", "decision_made"),
    }


def _active_workflow_stage(stage_counts: dict) -> str:
    for stage in WORKFLOW_STAGE_PRIORITY:
        if stage_counts.get(stage, 0) > 0:
            return stage
    return "inquiry"


def _build_follow_up_summary(apps: Any, stage_facts: dict[str, Any]) -> dict[str, Any]:
    now = timezone.now()
    stale_counts = {
        "application_submitted": 0,
        "in_review": 0,
        "accepted": 0,
    }
    thresholds = {
        "application_submitted": 3,
        "in_review": 5,
        "accepted": 2,
    }

    for app in apps:
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in stage_facts["inquiry"]),
            has_tour_scheduled=(app.id in stage_facts["tour_scheduled"]),
            has_tour_completed=(app.id in stage_facts["tour_completed"]),
            decision=stage_facts["decision"].get(app.id),
            enrolled=(app.id in stage_facts["enrolled"]),
        )
        threshold = thresholds.get(stage)
        if threshold is None:
            continue
        reference_at = app.updated_at or app.created_at
        if reference_at and reference_at <= now - timedelta(days=threshold):
            stale_counts[stage] += 1

    total_stale = sum(stale_counts.values())
    severity = "none"
    if total_stale >= 8:
        severity = "high"
    elif total_stale >= 3:
        severity = "medium"
    elif total_stale > 0:
        severity = "low"

    escalation = {
        "enabled": total_stale > 0,
        "severity": severity,
        "trigger": "no_response_detected" if total_stale > 0 else "none",
        "target": "admissions_follow_up_queue",
        "suggested_action": (
            "Escalate stale applications to coordinator queue and trigger same-day outreach."
            if total_stale > 0
            else "No escalation needed."
        ),
    }

    return {
        "stale_counts": stale_counts,
        "total_stale": total_stale,
        "aging_threshold_days": thresholds,
        "no_response_escalation": escalation,
    }


def _build_stage_aging(apps: Any, stage_facts: dict[str, Any]) -> dict[str, Any]:
    """Return age and SLA pressure for the operational admissions stages."""
    now = timezone.now()
    thresholds = {
        "application_submitted": 3,
        "in_review": 5,
        "accepted": 2,
    }
    buckets = {
        stage: {"count": 0, "over_sla": 0, "max_days": 0, "threshold_days": threshold}
        for stage, threshold in thresholds.items()
    }

    for app in apps:
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in stage_facts["inquiry"]),
            has_tour_scheduled=(app.id in stage_facts["tour_scheduled"]),
            has_tour_completed=(app.id in stage_facts["tour_completed"]),
            decision=stage_facts["decision"].get(app.id),
            enrolled=(app.id in stage_facts["enrolled"]),
        )
        bucket = buckets.get(stage)
        if bucket is None:
            continue
        reference_at = app.updated_at or app.created_at
        age_days = max(0, (now - reference_at).days) if reference_at else 0
        bucket["count"] += 1
        bucket["max_days"] = max(bucket["max_days"], age_days)
        if age_days >= bucket["threshold_days"]:
            bucket["over_sla"] += 1

    return buckets


def _latest_predictive_snapshot(school_id: Any) -> dict[str, Any]:
    """Expose existing auditable enrollment/retention model output without rerunning models."""
    snapshot = {
        "enrollment_forecast": None,
        "retention_support": None,
    }
    try:
        from analytics.models import PredictiveModelRun
        from analytics.predictors import ENROLLMENT_MODEL_NAME, RETENTION_MODEL_NAME
    except Exception:
        return snapshot

    for key, model_name in (
        ("enrollment_forecast", ENROLLMENT_MODEL_NAME),
        ("retention_support", RETENTION_MODEL_NAME),
    ):
        run = (
            PredictiveModelRun.objects.filter(school_id=school_id, model_name=model_name)
            .only("run_date", "output_json")
            .order_by("-run_date")
            .first()
        )
        if run is not None:
            snapshot[key] = {
                "run_date": run.run_date.isoformat(),
                "result": run.output_json or {},
            }
    return snapshot


def _build_enrollment_command_intelligence(
    *,
    school_id: Any,
    stage_counts: dict[str, Any],
    workflow_engine: dict[str, Any],
    post_admission_rollup: dict[str, Any],
    top_sources: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build a concise action queue from existing admissions and analytics truth."""
    stale_counts = workflow_engine.get("stale_counts") or {}
    accepted_pending = int(
        (post_admission_rollup.get("counts") or {}).get("accepted_pending_enrollment", 0) or 0
    )
    actions: list[dict[str, Any]] = []

    if int(stale_counts.get("application_submitted", 0) or 0) > 0:
        count = int(stale_counts["application_submitted"])
        actions.append({
            "priority": "high",
            "key": "review_submitted",
            "count": count,
            "label": f"Review {count} submitted application(s) over SLA.",
            "route": "/admissions/pipeline",
        })
    if int(stale_counts.get("in_review", 0) or 0) > 0:
        count = int(stale_counts["in_review"])
        actions.append({
            "priority": "high",
            "key": "advance_review",
            "count": count,
            "label": f"Advance {count} in-review application(s) over SLA.",
            "route": "/admissions/pipeline",
        })
    if accepted_pending > 0:
        actions.append({
            "priority": "high",
            "key": "accepted_to_enrolled",
            "count": accepted_pending,
            "label": f"Complete contract/deposit follow-up for {accepted_pending} accepted family/families.",
            "route": "/enrollment-conversion",
        })
    if int(stage_counts.get("inquiry", 0) or 0) > 0:
        count = int(stage_counts["inquiry"])
        actions.append({
            "priority": "normal",
            "key": "advance_inquiries",
            "count": count,
            "label": f"Advance {count} active inquiry/inquiries toward a tour or application.",
            "route": "/admissions/pipeline",
        })

    predictive = _latest_predictive_snapshot(school_id)
    return {
        "action_queue": actions[:6],
        "top_source": top_sources[0] if top_sources else None,
        "predictive": predictive,
        "guardrail": (
            "Retention output is a support indicator for proactive follow-up, not a prediction "
            "of an individual family's decision."
        ),
    }


def _build_workflow_engine_summary(stage_counts: dict[str, Any], stage_facts: dict[str, Any], apps: Any) -> dict[str, Any]:
    active_stage = _active_workflow_stage(stage_counts)
    guidance = WORKFLOW_STAGE_GUIDANCE.get(active_stage, WORKFLOW_STAGE_GUIDANCE["inquiry"])
    follow_up = _build_follow_up_summary(apps, stage_facts)
    return {
        "active_stage": active_stage,
        "active_stage_label": guidance["label"],
        "family_next_step": guidance["family_next_step"],
        "staff_next_step": guidance["staff_next_step"],
        "owner_team": "Admissions",
        "target_sla": guidance["target_sla"],
        **follow_up,
    }


def _accepted_application_ids(apps, stage_facts: dict) -> set[str]:
    accepted_ids: set[str] = set()
    for app in apps:
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in stage_facts["inquiry"]),
            has_tour_scheduled=(app.id in stage_facts["tour_scheduled"]),
            has_tour_completed=(app.id in stage_facts["tour_completed"]),
            decision=stage_facts["decision"].get(app.id),
            enrolled=(app.id in stage_facts["enrolled"]),
        )
        if stage == "accepted":
            accepted_ids.add(str(app.id))
    return accepted_ids


def _build_finance_readiness_summary(*, school_id: Any, accepted_app_ids: set[str]) -> dict[str, Any]:
    summary = {
        "source": "finance_obligations",
        "module_available": False,
        "admissions_fee_obligations_total": 0,
        "admissions_fee_obligations_paid": 0,
        "admissions_fee_obligations_unsettled": 0,
    }

    if not accepted_app_ids:
        summary["module_available"] = True
        return summary

    try:
        from finance.models import FinanceObligation, MoneyStatus
    except Exception:
        return summary

    obligations = FinanceObligation.objects.filter(
        school_id=school_id,
        reference__startswith="admissions_fee:",
    ).only("status", "reference")

    paid = 0
    unsettled = 0
    total = 0
    for obligation in obligations:
        reference = str(obligation.reference or "")
        _, _, app_id = reference.partition(":")
        if app_id not in accepted_app_ids:
            continue
        total += 1
        if obligation.status == MoneyStatus.PAID:
            paid += 1
        else:
            unsettled += 1

    summary.update(
        {
            "module_available": True,
            "admissions_fee_obligations_total": total,
            "admissions_fee_obligations_paid": paid,
            "admissions_fee_obligations_unsettled": unsettled,
        }
    )
    return summary


def _build_post_admission_rollup(*, school_id: Any, stage_counts: dict[str, Any], apps: Any, stage_facts: dict[str, Any]) -> dict[str, Any]:
    accepted = int(stage_counts.get("accepted", 0) or 0)
    waitlisted = int(stage_counts.get("waitlisted", 0) or 0)
    declined = int(stage_counts.get("declined", 0) or 0)
    enrolled = int(stage_counts.get("enrolled", 0) or 0)
    accepted_pending_enrollment = max(accepted - enrolled, 0)
    accepted_app_ids = _accepted_application_ids(apps=apps, stage_facts=stage_facts)
    finance_readiness = _build_finance_readiness_summary(
        school_id=school_id,
        accepted_app_ids=accepted_app_ids,
    )

    aid_or_billing_queue = max(
        accepted_pending_enrollment,
        int(finance_readiness.get("admissions_fee_obligations_unsettled", 0) or 0),
    )

    if accepted_pending_enrollment > 0:
        active_stage = "enrollment_contract"
    elif enrolled > 0:
        active_stage = "onboarding"
    else:
        active_stage = "admission_decision"

    return {
        "active_stage": active_stage,
        "dominant_pattern": [
            "admission_decision",
            "financial_aid",
            "enrollment_contract",
            "tuition_billing_setup",
            "onboarding",
            "sis_activation",
        ],
        "counts": {
            "admission_decision": accepted + waitlisted + declined,
            "accepted": accepted,
            "accepted_pending_enrollment": accepted_pending_enrollment,
            "financial_aid_or_billing": aid_or_billing_queue,
            "onboarding": enrolled,
            "sis_activation": enrolled,
        },
        "finance_readiness": finance_readiness,
        "stages": [
            {
                "key": "admission_decision",
                "label": "Admission Decision",
                "owner_team": "Admissions",
                "total": accepted + waitlisted + declined,
            },
            {
                "key": "financial_aid",
                "label": "Financial Aid",
                "owner_team": "Financial Aid",
                "total": aid_or_billing_queue,
            },
            {
                "key": "enrollment_contract",
                "label": "Enrollment Contract",
                "owner_team": "Admissions",
                "total": accepted_pending_enrollment,
            },
            {
                "key": "tuition_billing_setup",
                "label": "Tuition and Billing Setup",
                "owner_team": "Finance",
                "total": aid_or_billing_queue,
            },
            {
                "key": "onboarding",
                "label": "Onboarding",
                "owner_team": "Student Services",
                "total": enrolled,
            },
            {
                "key": "sis_activation",
                "label": "SIS Activation",
                "owner_team": "Registrar",
                "total": enrolled,
            },
        ],
    }


def _parse_pagination(request):
    try:
        limit = int(request.query_params.get("limit", "25"))
        offset = int(request.query_params.get("offset", "0"))
    except ValueError:
        return None, None, Response({"detail": "limit and offset must be integers"}, status=400)
    if limit < 1 or limit > 200 or offset < 0:
        return None, None, Response(
            {"detail": "limit must be 1..200 and offset must be >= 0"}, status=400
        )
    return limit, offset, None


def _build_drilldown_rows(apps, applicants_qs, stage_facts: dict, stage_filter: str | None):
    rows = []
    apps_by_id = {a.id: a for a in apps}
    for applicant in applicants_qs.select_related("application"):
        app = apps_by_id.get(applicant.application_id)
        if not app:
            continue
        stage = _compute_stage(
            app=app,
            has_inquiry=(app.id in stage_facts["inquiry"]),
            has_tour_scheduled=(app.id in stage_facts["tour_scheduled"]),
            has_tour_completed=(app.id in stage_facts["tour_completed"]),
            decision=stage_facts["decision"].get(app.id),
            enrolled=(app.id in stage_facts["enrolled"]),
        )
        if stage_filter and stage != stage_filter:
            continue
        flags = applicant.flags or {}
        rows.append(
            {
                "lead_id": str(applicant.id),
                "application_id": str(app.id),
                "student_id": str(applicant.student_id) if applicant.student_id else None,
                "stage": stage,
                "source": applicant.source or "other",
                "grade_applying_for": applicant.grade_applying_for,
                "created_at": app.created_at.isoformat(),
                "updated_at": app.updated_at.isoformat(),
                "flags": {
                    "duplicate_suspected": bool(flags.get("duplicate_suspected", False)),
                    "bot_suspected": bool(flags.get("bot_suspected", False)),
                },
            }
        )
    return rows


@extend_schema(responses=AdmissionsPublicConfigResponseSerializer)
@api_view(["GET"])
@permission_classes([AllowAny])
def admissions_public_config(_request):
    return Response(
        {
            "application_fee": _application_fee_config(),
            "assessment_interview": _assessment_interview_config(),
        }
    )


def _resolve_school(request):
    """
    Resolve tenant school for admissions endpoints.

    Normal path uses request.school populated by TenantHeaderRequiredMiddleware.
    In some test/dev contexts tenant enforcement is disabled, so we fall back to
    the shared resolver to preserve header-based contracts.
    """
    school = getattr(request, "school", None)
    if school is not None:
        return school, None

    resolved = resolve_tenant_school_id(request)
    school_id = resolved.school_id

    if resolved.source == "header_invalid":
        return None, Response(
            {
                "detail": "Invalid X-School-Id (must be UUID).",
                "code": "invalid_tenant_header",
            },
            status=400,
        )

    if not school_id:
        return None, Response(
            {
                "detail": "Missing required header: X-School-Id.",
                "code": "missing_tenant",
            },
            status=400,
        )

    school = School.objects.filter(pk=school_id).only("id", "name").first()
    if school is None:
        return None, Response(
            {
                "detail": "Unknown X-School-Id.",
                "code": "invalid_tenant",
            },
            status=404,
        )

    request.school = school
    request.school_id = str(school.id)
    return school, None


def _resolve_school_for_submit(request: Any, payload: dict[str, Any]):
    school, tenant_error = _resolve_school(request)
    if school is not None:
        return school, None

    error_code = (tenant_error.data or {}).get("code") if hasattr(tenant_error, "data") else None
    if error_code == "invalid_tenant_header":
        return None, tenant_error

    inquiry = payload.get("inquiry") or {}
    campus = str(inquiry.get("campus") or "").strip()
    if not campus:
        return None, _validation_error(
            "Missing required header: X-School-Id. Provide inquiry.campus for public submit routing.",
            code="missing_tenant",
        )

    school = School.objects.filter(name__iexact=campus).only("id", "name").first()
    if school is None:
        school = School.objects.filter(name__icontains=campus).only("id", "name").first()

    if school is None:
        return None, Response(
            {
                "detail": f"Unable to resolve school for campus '{campus}'.",
                "code": "invalid_tenant",
            },
            status=404,
        )

    request.school = school
    request.school_id = str(school.id)
    return school, None


def _request_payload_or_empty(request: Any) -> dict[str, Any]:
    try:
        payload = request.data or {}
    except Exception:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _normalize_checklist_token(value: Any) -> str:
    token = str(value or "").strip()
    if token.lower() in {"none", "null", "undefined"}:
        return ""
    if not token:
        return ""
    try:
        return str(uuid.UUID(token))
    except Exception:
        return ""


def _checklist_application_error(application_id: str, checklist_key: str, tenant_school_id: str | None) -> Response | None:
    if not application_id and not checklist_key:
        return Response({"detail": "application_id or checklist_key is required."}, status=400)
    if application_id and not checklist_key and not tenant_school_id:
        return Response(
            {
                "detail": "application_id without checklist_key requires X-School-Id.",
                "code": "missing_tenant",
            },
            status=400,
        )
    return None


def _lookup_checklist_application(tenant_school_id: str | None, application_id: str, checklist_key: str) -> Application | None:
    filters: dict[str, Any] = {}
    if checklist_key:
        filters["checklist_access_key"] = checklist_key
    if tenant_school_id:
        filters["school_id"] = tenant_school_id
    if application_id and checklist_key:
        filters["id"] = application_id
        return Application.objects.filter(**filters).first()
    if application_id:
        return Application.objects.filter(school_id=tenant_school_id, id=application_id).first()
    if checklist_key:
        return Application.objects.filter(**filters).first()
    return None


def _resolve_submission_artifacts(
    *,
    school: School,
    applications: list[Application],
    applicants: list[Applicant],
) -> tuple[list[str], list[str], Application | None, list[ApplicationChecklistItem]]:
    application_ids = [str(app.id) for app in applications]
    applicant_ids = [str(applicant.id) for applicant in applicants]
    first_application = applications[0] if applications else None
    if first_application is None:
        first_application = Application.objects.filter(school_id=school.pk).order_by("-created_at").first()
    if first_application is not None and not application_ids:
        application_ids = [str(first_application.id)]
    if first_application is not None:
        first_applicant = first_application.applicants.order_by("created_at").first()
        if first_applicant is not None:
            applicant_ids = [str(first_applicant.id)]

    checklist_items = list(first_application.checklist_items.prefetch_related("documents").all()) if first_application else []
    return application_ids, applicant_ids, first_application, checklist_items


def _auto_complete_demo_checklists(applications: list[Application], enabled: bool) -> None:
    if not enabled:
        return
    for app in applications:
        _promote_checklist_for_demo(app)


def _validate_enrollment_state_update_request(
    *,
    app: Application,
    current: dict[str, Any],
    requested_contract: Any,
    requested_deposit: Any,
) -> Response | None:
    if requested_contract not in CONTRACT_TRANSITIONS:
        return Response({"detail": "Invalid contract_status."}, status=400)
    if requested_deposit not in DEPOSIT_TRANSITIONS:
        return Response({"detail": "Invalid deposit_status."}, status=400)
    if not _application_is_post_acceptance(app):
        return Response(
            {
                "detail": "Enrollment contract/deposit states can be updated only after acceptance.",
                "application_status": app.status,
            },
            status=409,
        )

    contract_error = _validate_state_transition(
        current=current["contract_status"],
        requested=requested_contract,
        graph=CONTRACT_TRANSITIONS,
        state_name="contract_status",
    )
    if contract_error:
        return Response({"detail": contract_error}, status=409)

    deposit_error = _validate_state_transition(
        current=current["deposit_status"],
        requested=requested_deposit,
        graph=DEPOSIT_TRANSITIONS,
        state_name="deposit_status",
    )
    if deposit_error:
        return Response({"detail": deposit_error}, status=409)

    return None


def _resolve_checklist_application_impl(request):
    request_payload = _request_payload_or_empty(request) if request.method != "GET" else {}
    application_id = _normalize_checklist_token(
        request.query_params.get("application_id") or request_payload.get("application_id")
    )
    checklist_key = _normalize_checklist_token(
        request.query_params.get("checklist_key")
        or request.headers.get("X-Checklist-Key")
        or request_payload.get("checklist_key")
    )
    resolved = resolve_tenant_school_id(request)
    tenant_school_id = resolved.school_id
    if resolved.source == "header_invalid":
        return None, Response(
            {
                "detail": "Invalid X-School-Id (must be UUID).",
                "code": "invalid_tenant_header",
            },
            status=400,
        )

    access_error = _checklist_application_error(application_id, checklist_key, tenant_school_id)
    if access_error is not None:
        return None, access_error

    app = _lookup_checklist_application(tenant_school_id, application_id, checklist_key)

    if app is None:
        return None, Response({"detail": "Checklist access denied."}, status=404)

    return app, None


def _resolve_checklist_application(request):
    return _resolve_checklist_application_impl(request)


@api_view(["GET"])
@permission_classes([AllowAny])
def admissions_checklist_hub(request):
    app, error = _resolve_checklist_application(request)
    if error is not None:
        return error
    assert app is not None

    items = list(
        app.checklist_items.prefetch_related("documents").order_by("office", "title")
    )

    if not items:
        applicant = Applicant.objects.filter(application=app).first()
        documents = {}
        if applicant and isinstance(applicant.flags, dict):
            documents = applicant.flags.get("documents") or {}
        _ensure_application_checklist_items(app, documents)
        items = list(app.checklist_items.prefetch_related("documents").order_by("office", "title"))

    grouped = {}
    for item in items:
        grouped.setdefault(item.office, []).append(_serialize_checklist_item(item))

    demo_flow = str(request.query_params.get("demo_flow") or "").strip() in {"1", "true", "True"}

    return Response(
        {
            "application_id": str(app.id),
            "status": app.status,
            "summary": _checklist_summary(items),
            "groups": grouped,
            "items": [_serialize_checklist_item(item) for item in items],
            "next_step_orchestration": _build_next_step_orchestration(
                checklist_items=items,
                demo_completed=demo_flow,
            ),
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def admissions_checklist_upload(request, item_id):
    app, error = _resolve_checklist_application(request)
    if error is not None:
        return error

    checklist_item = ApplicationChecklistItem.objects.filter(
        application=app,
        id=item_id,
    ).first()
    if checklist_item is None:
        return Response({"detail": "Checklist item not found."}, status=404)

    upload = request.FILES.get("file")
    if upload is None:
        return Response({"detail": "file is required."}, status=400)

    uploaded_by = str((request.data or {}).get("uploaded_by") or "").strip()[:255]
    created_doc = ApplicationChecklistDocument.objects.create(
        school_id=app.school_id,
        checklist_item=checklist_item,
        file=upload,
        original_filename=getattr(upload, "name", "upload"),
        content_type=str(getattr(upload, "content_type", "") or "")[:120],
        uploaded_by=uploaded_by,
    )

    quality_status, quality_note = _infer_document_quality_status(
        filename=created_doc.original_filename,
        content_type=created_doc.content_type,
    )

    checklist_item.status = ChecklistItemStatus.SUBMITTED
    checklist_item.submitted_at = timezone.now()
    checklist_item.notes = quality_note
    checklist_item.save(update_fields=["status", "submitted_at", "notes", "updated_at"])

    items = list(app.checklist_items.prefetch_related("documents").order_by("office", "title"))
    return Response(
        {
            "ok": True,
            "application_id": str(app.id),
            "item": _serialize_checklist_item(checklist_item),
            "summary": _checklist_summary(items),
            "document_quality": {
                "status": quality_status,
                "note": quality_note,
            },
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_summary(request):
    """GET /api/v1/admissions/summary/ - Pipeline KPIs for admissions director."""
    from core.permissions import user_has_permission
    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_VIEW_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)
    school_id = school.pk

    academic_year = request.query_params.get("academic_year")
    date_from = (
        parse_date(request.query_params.get("date_from"))
        if request.query_params.get("date_from")
        else None
    )
    date_to = (
        parse_date(request.query_params.get("date_to"))
        if request.query_params.get("date_to")
        else None
    )

    ay_name, ay_start, ay_end, ay_explicit = _get_academic_year_window(school_id, academic_year)

    apps = Application.objects.filter(school_id=school_id)

    # Academic year date filter only if academic_year param was explicitly provided
    # This prevents "seeded data but shows 0" when data.created_at is outside AY window
    if ay_explicit and ay_start and ay_end:
        apps = apps.filter(created_at__date__gte=ay_start, created_at__date__lte=ay_end)

    # Optional date window override
    if date_from:
        apps = apps.filter(created_at__date__gte=date_from)
    if date_to:
        apps = apps.filter(created_at__date__lte=date_to)

    app_ids = list(apps.values_list("id", flat=True))
    pipeline_total = len(app_ids)

    events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)
    stage_facts = _collect_stage_facts(events)
    stage_counts = _build_stage_counts(apps, stage_facts)
    conversion = _build_conversion_rates(stage_counts)
    velocity = _build_velocity(events)
    workflow_engine = _build_workflow_engine_summary(apps=apps, stage_counts=stage_counts, stage_facts=stage_facts)
    stage_aging = _build_stage_aging(apps=apps, stage_facts=stage_facts)
    post_admission_rollup = _build_post_admission_rollup(
        school_id=school_id,
        stage_counts=stage_counts,
        apps=apps,
        stage_facts=stage_facts,
    )

    # Top sources — from Applicant.source (canonical)
    applicants = Applicant.objects.filter(school_id=school_id, application_id__in=app_ids)
    top_sources_qs = (
        applicants.values("source")
        .annotate(total=Count("id"))
        .order_by("-total", "source")[:10]
    )
    top_sources = [{"source": r["source"], "total": r["total"]} for r in top_sources_qs]
    command_intelligence = _build_enrollment_command_intelligence(
        school_id=school_id,
        stage_counts=stage_counts,
        workflow_engine=workflow_engine,
        post_admission_rollup=post_admission_rollup,
        top_sources=top_sources,
    )

    return Response(
        {
            "academic_year": ay_name,
            "date_from": request.query_params.get("date_from"),
            "date_to": request.query_params.get("date_to"),
            "pipeline": {"total": pipeline_total, "by_stage": stage_counts},
            "conversion": conversion,
            "velocity_days": velocity,
            "stage_aging": stage_aging,
            "top_sources": top_sources,
            "workflow_engine": workflow_engine,
            "post_admission_rollup": post_admission_rollup,
            "command_intelligence": command_intelligence,
        }
    )


def _admissions_submit_impl(request):
    """POST /api/v1/admissions/submit/ - Persist public admissions wizard submission."""
    correlation_id = _request_correlation_id(request)
    trace_id = _request_trace_id(request)
    payload = request.data or {}
    demo_checklist_auto_complete = bool(payload.get("demoChecklistAutoComplete"))
    school, tenant_error = _resolve_school_for_submit(request, payload)
    if tenant_error is not None:
        return _attach_correlation(tenant_error, correlation_id)

    abuse_error = _enforce_submit_abuse_controls(request, school.pk, payload, correlation_id)
    if abuse_error is not None:
        return abuse_error

    idempotency_key = _idempotency_key(request)
    if idempotency_key:
        cached_response = cache.get(_cache_key_for_submit(school.pk, idempotency_key))
        if cached_response:
            replay = Response(cached_response, status=200)
            replay["X-Idempotent-Replay"] = "true"
            return _attach_correlation(replay, correlation_id)

    submit_data = _extract_submit_data(payload)
    validation_error = _validate_submit_data(submit_data)
    if validation_error:
        return _attach_correlation(
            _validation_error(validation_error, correlation_id=correlation_id),
            correlation_id,
        )

    applications, applicants = _create_admissions_submission_records(school.pk, submit_data)
    communications_dispatch = _queue_family_communications(
        school_id=school.pk,
        guardians=submit_data.guardians,
        application_ids=[str(app.id) for app in applications],
        correlation_id=correlation_id,
        stage_token="application_submitted",
    )
    _auto_complete_demo_checklists(applications, demo_checklist_auto_complete)
    application_ids, applicant_ids, first_application, checklist_items = _resolve_submission_artifacts(
        school=school,
        applications=applications,
        applicants=applicants,
    )

    application_fee = _create_application_fee_finance_records(
        school=school,
        data=submit_data,
        application_ids=application_ids,
        correlation_id=correlation_id,
    )

    response_payload = {
        "ok": True,
        "trace_id": trace_id,
        "application_id": application_ids[0] if application_ids else None,
        "applicant_id": applicant_ids[0] if applicant_ids else None,
        "application_ids": application_ids,
        "applicant_ids": applicant_ids,
        "application_count": len(application_ids),
        "stage": "application_submitted",
        "message": "Application submitted successfully.",
        "status_center": {
            "current_stage": "application_submitted",
            "owner_team": "Admissions",
            "owner_contact": {
                "phone": "(555) 010-1000",
                "email": "admissions@crown.edu",
            },
            "next_update_target": REVIEW_DECISION_SLA_TEXT,
            "family_next_step": WORKFLOW_STAGE_GUIDANCE["application_submitted"]["family_next_step"],
            "staff_next_step": WORKFLOW_STAGE_GUIDANCE["application_submitted"]["staff_next_step"],
            "decision_due_by": _decision_deadline_iso(),
            "milestones": _build_submit_milestones(submit_data),
        },
        "workflow_engine": {
            "active_stage": "application_submitted",
            "active_stage_label": WORKFLOW_STAGE_GUIDANCE["application_submitted"]["label"],
            "family_next_step": WORKFLOW_STAGE_GUIDANCE["application_submitted"]["family_next_step"],
            "staff_next_step": WORKFLOW_STAGE_GUIDANCE["application_submitted"]["staff_next_step"],
            "owner_team": "Admissions",
            "target_sla": WORKFLOW_STAGE_GUIDANCE["application_submitted"]["target_sla"],
        },
        "documents_lifecycle": _build_document_lifecycle(submit_data.documents),
        "assessment_interview": _build_assessment_interview_status(submit_data),
        "enrollment_continuity": _build_enrollment_continuity(submit_data),
        "post_admission_lifecycle": _build_post_admission_lifecycle(submit_data),
        "communications_dispatch": communications_dispatch,
        "reviewer_summary": _build_reviewer_summary(submit_data, applicants),
        "family_affordability_profile": _build_family_affordability_profile(
            data=submit_data,
            application_ids=application_ids,
            application_fee=application_fee,
        ),
        "application_fee": application_fee,
        "application_fee_status_card": _build_application_fee_status_card(application_fee=application_fee),
        "admissions_to_finance_handoff": _build_admissions_finance_handoff_panel(
            data=submit_data,
            application_fee=application_fee,
        ),
        "fee_config": _application_fee_config(),
        "checklist_hub": {
            "path": "/admissions/checklist",
            "application_id": application_ids[0] if application_ids else None,
            "checklist_key": str(first_application.checklist_access_key) if first_application else None,
            "summary": _checklist_summary(checklist_items),
        },
        "next_step_orchestration": _build_next_step_orchestration(
            checklist_items=checklist_items,
            demo_completed=demo_checklist_auto_complete,
        ),
        "enrollment_contract_automation": _build_contract_m365_handoff(application_ids=application_ids),
    }

    if idempotency_key:
        # Keep replay window short but long enough for user retries and browser retransmits.
        cache.set(
            _cache_key_for_submit(school.pk, idempotency_key),
            response_payload,
            timeout=10 * 60,
        )

    return _attach_correlation(Response(response_payload, status=201), correlation_id)


@extend_schema(responses=AdmissionsSubmitResponseSerializer)
@api_view(["POST"])
@permission_classes([AllowAny])
def admissions_submit(request):
    return _admissions_submit_impl(request)


@extend_schema(responses=AdmissionsDrilldownResponseSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_drilldown(request):
    """GET /api/v1/admissions/drilldown/ - Paginated lead details."""
    from core.permissions import user_has_permission
    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_VIEW_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)
    school_id = school.pk

    academic_year = request.query_params.get("academic_year")
    stage = request.query_params.get("stage")
    source = request.query_params.get("source")

    limit, offset, pagination_error = _parse_pagination(request)
    if pagination_error is not None:
        return pagination_error
    assert limit is not None and offset is not None

    if stage is not None and stage != "" and stage not in STAGES:
        return Response(
            {"detail": f"Invalid stage '{stage}'. Must be one of: {', '.join(STAGES)}."},
            status=400
        )

    ay_name, ay_start, ay_end, ay_explicit = _get_academic_year_window(school_id, academic_year)

    apps = Application.objects.filter(school_id=school_id)
    if ay_explicit and ay_start and ay_end:
        apps = apps.filter(created_at__date__gte=ay_start, created_at__date__lte=ay_end)

    app_ids = list(apps.values_list("id", flat=True))

    events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)
    stage_facts = _collect_stage_facts(events)

    # Query Applicants as the canonical "lead rows"
    qs = Applicant.objects.filter(school_id=school_id, application_id__in=app_ids)

    if source:
        qs = qs.filter(source=source)

    rows_all = _build_drilldown_rows(apps, qs, stage_facts, stage)

    total = len(rows_all)
    page = rows_all[offset : offset + limit]

    response = Response(
        {
            "academic_year": ay_name,
            "stage": stage or None,
            "source": source or None,
            "total": total,
            "limit": limit,
            "offset": offset,
            "rows": page,  # DEPRECATED: use 'results' instead
            "results": page,
        }
    )

    # Add deprecation warning header for clients still checking 'rows'
    response["X-Deprecated-Field"] = "rows; use results instead; sunset 2026-06-01"

    return response


@extend_schema(responses=AdmissionsEnrollmentStateResponseSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_enrollment_state(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_VIEW_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)
    assert school is not None

    state = _latest_enrollment_state_for_application(app)
    return Response(
        {
            "application_id": str(app.id),
            "application_status": app.status,
            **state,
        }
    )


def _admissions_enrollment_state_update_impl(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_EDIT_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)

    current = _latest_enrollment_state_for_application(app)
    requested_contract = (request.data or {}).get("contract_status") or current["contract_status"]
    requested_deposit = (request.data or {}).get("deposit_status") or current["deposit_status"]
    note = str((request.data or {}).get("note") or "").strip()[:500]
    transition_reason = str((request.data or {}).get("transition_reason") or "").strip()[:280]
    owner_assignment = str((request.data or {}).get("owner_assignment") or "").strip()[:180]
    trace_id = _request_trace_id(request)
    validation_error = _validate_enrollment_state_update_request(
        app=app,
        current=current,
        requested_contract=requested_contract,
        requested_deposit=requested_deposit,
    )
    if validation_error is not None:
        return validation_error

    contract_record, billing_handoff = _commit_enrollment_state_update(
        school=school,
        app=app,
        request_payload=request.data if isinstance(request.data, dict) else {},
        actor_user=request.user,
        requested_contract=requested_contract,
        requested_deposit=requested_deposit,
        note=note,
        transition_reason=transition_reason,
        owner_assignment=owner_assignment,
        trace_id=trace_id,
    )
    legacy_bridge = _upsert_legacy_admissions_applications(
        app=app,
        actor_user=request.user,
        target_status="ACCEPTED",
    )

    state = _latest_enrollment_state_for_application(app)
    return Response(
        {
            "application_id": str(app.id),
            "application_status": app.status,
            "contract_record": _serialize_enrollment_contract(contract_record),
            "billing_handoff": billing_handoff,
            "legacy_conversion_bridge": legacy_bridge,
            "transition_reason": transition_reason,
            "owner_assignment": owner_assignment,
            "trace_id": trace_id,
            **state,
        },
        status=200,
    )


@extend_schema(responses=AdmissionsEventReplayResponseSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_application_event_replay(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_VIEW_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)

    limit_raw = str(request.query_params.get("limit") or "50").strip()
    try:
        limit = max(1, min(int(limit_raw), 200))
    except Exception:
        return Response({"detail": "limit must be an integer 1..200"}, status=400)

    event_rows = list(
        ApplicationEvent.objects.filter(school_id=school.pk, application=app)
        .order_by("-created_at")
        .values("event_type", "payload", "created_at")[:limit]
    )
    return Response(
        {
            "application_id": str(app.id),
            "count": len(event_rows),
            "events": [
                {
                    "event_type": row["event_type"],
                    "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                    "payload": row.get("payload") or {},
                }
                for row in event_rows
            ],
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admissions_enrollment_state_update(request, application_id):
    return _admissions_enrollment_state_update_impl(request, application_id)


def _commit_enrollment_state_update(
    *,
    school,
    app: Application,
    request_payload: dict,
    actor_user,
    requested_contract: str,
    requested_deposit: str,
    note: str,
    transition_reason: str,
    owner_assignment: str,
    trace_id: str,
):
    ApplicationEvent.objects.create(
        school_id=school.pk,
        application=app,
        event_type=ENROLLMENT_STATE_EVENT_TYPE,
        payload={
            "contract_status": requested_contract,
            "deposit_status": requested_deposit,
            "note": note,
            "transition_reason": transition_reason,
            "owner_assignment": owner_assignment,
            "trace_id": trace_id,
            "updated_by": str(getattr(actor_user, "email", "") or getattr(actor_user, "username", "")),
        },
    )

    if owner_assignment:
        ApplicationEvent.objects.create(
            school_id=school.pk,
            application=app,
            event_type="admissions_owner_reassigned",
            payload={
                "owner_assignment": owner_assignment,
                "trace_id": trace_id,
                "updated_by": str(getattr(actor_user, "email", "") or getattr(actor_user, "username", "")),
            },
        )

    _safe_register_crm_workflow_update(
        app=app,
        contract_status=requested_contract,
        deposit_status=requested_deposit,
        user=actor_user,
        school_id=school.pk,
    )

    contract_payload = request_payload.get("contract") if isinstance(request_payload.get("contract"), dict) else {}
    contract_record = _upsert_contract_for_application(
        app=app,
        actor_user=actor_user,
        payload=cast(dict[str, Any], contract_payload),
        status_hint=_contract_status_from_enrollment_state(requested_contract),
    )
    billing_handoff = _ensure_billing_obligation_for_countersigned_contract(
        school=school,
        app=app,
        contract=contract_record,
        actor_user=actor_user,
    )

    ApplicationEvent.objects.create(
        school_id=school.pk,
        application=app,
        event_type="billing_handoff_updated",
        payload={
            "contract_id": str(contract_record.id),
            "contract_version": contract_record.version,
            "billing_handoff": billing_handoff,
        },
    )
    return contract_record, billing_handoff


@extend_schema(responses=AdmissionsContractDetailResponseSerializer)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_contract_detail(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_VIEW_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)

    contract = _latest_contract_for_application(app)
    if contract is None:
        return Response(
            {
                "application_id": str(app.id),
                "contract": None,
                "history": [],
            },
            status=200,
        )

    history = [
        _serialize_enrollment_contract(row)
        for row in EnrollmentContract.objects.filter(school_id=school.pk, application=app).order_by("-version")
    ]
    return Response(
        {
            "application_id": str(app.id),
            "contract": _serialize_enrollment_contract(contract),
            "history": history,
        }
    )


@extend_schema(responses=AdmissionsContractUpdateResponseSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admissions_contract_update(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_EDIT_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)

    payload = request.data if isinstance(request.data, dict) else {}
    contract = _upsert_contract_for_application(
        app=app,
        actor_user=request.user,
        payload=payload,
    )
    billing_handoff = _ensure_billing_obligation_for_countersigned_contract(
        school=school,
        app=app,
        contract=contract,
        actor_user=request.user,
    )
    ApplicationEvent.objects.create(
        school_id=school.pk,
        application=app,
        event_type="contract_updated",
        payload={
            "contract_id": str(contract.id),
            "contract_version": contract.version,
            "status": contract.status,
        },
    )

    return Response(
        {
            "application_id": str(app.id),
            "contract": _serialize_enrollment_contract(contract),
            "billing_handoff": billing_handoff,
        },
        status=200,
    )


@extend_schema(responses=AdmissionsContractAmendResponseSerializer)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admissions_contract_amend(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_EDIT_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)

    latest = _latest_contract_for_application(app)
    if latest is None:
        return Response({"detail": "No contract exists to amend."}, status=409)

    payload = request.data if isinstance(request.data, dict) else {}
    amended_line_items = _normalize_contract_line_items(payload.get("line_items"))
    if not amended_line_items:
        amended_line_items = latest.line_items or []
    amended_totals = _compute_contract_totals(amended_line_items, payload.get("totals") or latest.contract_totals)

    latest.status = EnrollmentContractStatus.SUPERSEDED
    latest.save(update_fields=["status", "updated_at"])

    amended = EnrollmentContract.objects.create(
        school_id=app.school_id,
        application=app,
        version=latest.version + 1,
        status=EnrollmentContractStatus.ISSUED,
        line_items=amended_line_items,
        contract_totals=amended_totals,
        net_amount_cents=amended_totals.get("net_family_obligation_cents", 0),
        currency=latest.currency,
        payment_plan=str(payload.get("payment_plan") or latest.payment_plan or "")[:80],
        payment_schedule=str(payload.get("payment_schedule") or latest.payment_schedule or "")[:255],
        responsible_payer=str(payload.get("responsible_payer") or latest.responsible_payer or "")[:255],
        refund_terms=str(payload.get("refund_terms") or latest.refund_terms or "")[:2000],
        note=str(payload.get("note") or payload.get("amendment_reason") or "Contract amended")[:2000],
        issued_at=timezone.now(),
        amended_from=latest,
        created_by=str(getattr(request.user, "email", "") or getattr(request.user, "username", ""))[:255],
    )

    ApplicationEvent.objects.create(
        school_id=school.pk,
        application=app,
        event_type="contract_amended",
        payload={
            "from_contract_id": str(latest.id),
            "to_contract_id": str(amended.id),
            "from_version": latest.version,
            "to_version": amended.version,
            "amendment_reason": amended.note,
        },
    )

    return Response(
        {
            "application_id": str(app.id),
            "contract": _serialize_enrollment_contract(amended),
        },
        status=200,
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def admissions_lifecycle_chain_update(request, application_id):
    from core.permissions import user_has_permission

    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, ADMISSIONS_EDIT_PERMISSION, school=school):
        return Response({"detail": PERMISSION_DENIED_DETAIL}, status=403)

    app = Application.objects.filter(school_id=school.pk, id=application_id).first()
    if app is None:
        return Response({"detail": APPLICATION_NOT_FOUND_DETAIL}, status=404)
    if not _application_is_post_acceptance(app):
        return Response(
            {"detail": "Lifecycle handoff can be updated only after acceptance.", "application_status": app.status},
            status=409,
        )

    payload = request.data if isinstance(request.data, dict) else {}
    note = str(payload.get("note") or "").strip()[:500]
    created_events, error = _apply_lifecycle_chain_updates(
        app=app,
        actor_user=request.user,
        note=note,
        request_payload=payload,
    )
    if error is not None:
        return error

    target_status = "ENROLLED" if ENROLLMENT_CONFIRMED_EVENT_TYPE in (created_events or []) or _application_has_event(app, ENROLLMENT_CONFIRMED_EVENT_TYPE) else "ACCEPTED"
    legacy_bridge = _upsert_legacy_admissions_applications(
        app=app,
        actor_user=request.user,
        target_status=target_status,
    )

    state = _latest_enrollment_state_for_application(app)
    return Response(
        {
            "application_id": str(app.id),
            "application_status": app.status,
            "created_events": created_events or [],
            "legacy_conversion_bridge": legacy_bridge,
            **state,
        },
        status=200,
    )
