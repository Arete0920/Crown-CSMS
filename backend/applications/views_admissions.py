from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model

from django.db.models import Count, Min
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.models import AcademicYear, School
from crown_api.tenant import resolve_tenant_school_id
from households.models import Household
from .models import Application, Applicant, ApplicationEvent


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
APPLICATION_FEE_CURRENCY = "USD"
SUBMIT_IP_RATE_LIMIT = 30
SUBMIT_IP_RATE_WINDOW_SECONDS = 15 * 60
SUBMIT_EMAIL_RATE_LIMIT = 6
SUBMIT_EMAIL_RATE_WINDOW_SECONDS = 60 * 60


def _application_fee_required() -> bool:
    return APPLICATION_FEE_USD > Decimal("0")


def _application_fee_config() -> dict:
    return {
        "required": _application_fee_required(),
        "amount": str(APPLICATION_FEE_USD),
        "currency": APPLICATION_FEE_CURRENCY,
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


def _validation_error(detail: str, code: str = "invalid_request", correlation_id: str | None = None):
    payload = {
        "detail": detail,
        "message": detail,
        "code": code,
    }
    if correlation_id:
        payload["correlation_id"] = correlation_id
    return Response(payload, status=400)


def _request_correlation_id(request) -> str:
    header_value = (
        request.headers.get("X-Request-Id")
        or request.headers.get("X-Correlation-Id")
        or ""
    ).strip()
    return header_value[:128] if header_value else str(uuid.uuid4())


def _idempotency_key(request) -> str:
    value = (
        request.headers.get("Idempotency-Key")
        or request.headers.get("X-Idempotency-Key")
        or ""
    ).strip()
    return value[:256]


def _cache_key_for_submit(school_id, idempotency_key: str) -> str:
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


def _client_ip_address(request) -> str:
    forwarded = str(request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    remote = str(request.META.get("REMOTE_ADDR") or "").strip()
    return forwarded or remote or "unknown"


def _primary_guardian_email(payload: dict) -> str:
    family = payload.get("family") if isinstance(payload.get("family"), dict) else {}
    guardians = family.get("guardians") if isinstance(family.get("guardians"), list) else []
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


def _enforce_submit_abuse_controls(request, school_id, payload: dict, correlation_id: str) -> Response | None:
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
    if isinstance(response.data, dict):
        response.data.setdefault("correlation_id", correlation_id)
    return response


@dataclass
class AdmissionsSubmitData:
    inquiry: dict
    family: dict
    guardians: list[dict]
    students: list[dict]
    mission: dict
    documents: dict
    attestations: dict
    application_fee: dict
    campus: str
    start_term: str


def _build_legacy_guardian(family: dict) -> dict | None:
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


def _extract_guardians(family: dict) -> list[dict]:
    guardians = family.get("guardians") if isinstance(family.get("guardians"), list) else []
    if guardians:
        return guardians
    legacy_guardian = _build_legacy_guardian(family)
    return [legacy_guardian] if legacy_guardian else []


def _extract_students(payload: dict) -> list[dict]:
    students_value = payload.get("students")
    if isinstance(students_value, list) and students_value:
        return students_value
    legacy_student = payload.get("student") or {}
    return [legacy_student] if legacy_student else []


def _extract_submit_data(payload: dict) -> AdmissionsSubmitData:
    inquiry = payload.get("inquiry") or {}
    family = payload.get("family") or {}
    students = _extract_students(payload)
    guardians = _extract_guardians(family)

    mission = payload.get("mission") or {}
    documents = payload.get("documents") or {}
    attestations = payload.get("attestations") or {}
    application_fee = payload.get("applicationFee") or {}
    return AdmissionsSubmitData(
        inquiry=inquiry,
        family=family,
        guardians=guardians,
        students=students,
        mission=mission,
        documents=documents,
        attestations=attestations,
        application_fee=application_fee,
        campus=str(inquiry.get("campus") or "").strip(),
        start_term=str(inquiry.get("startTerm") or "").strip(),
    )


def _validate_guardian(guardian: dict, index: int) -> str | None:
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


def _validate_student(student: dict, index: int) -> str | None:
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


def _create_admissions_submission_records(school_id, data: AdmissionsSubmitData):
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

            applicant_flags = {
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
                "student_strengths": student.get("strengths") or "",
                "support_needs": student.get("supportNeeds") or "",
                "mission": data.mission,
                "documents": data.documents,
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

            applications.append(application)
            applicants.append(applicant)

    return applications, applicants


def _build_document_lifecycle(documents: dict) -> list[dict]:
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


def _build_submit_milestones() -> list[dict]:
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
            "target": "Within 1 business day",
            "status": "in_progress",
        },
        {
            "key": "readiness_review",
            "title": "Readiness and Mission Review",
            "target": "Within 2 business days",
            "status": "pending",
        },
        {
            "key": "next_step_scheduling",
            "title": "Tour / Interview Scheduling",
            "target": "Within 3-5 business days",
            "status": "pending",
        },
    ]


def _application_fee_status_value(fee_required: bool, waiver_requested: bool) -> str:
    if waiver_requested:
        return "waiver_requested"
    if fee_required:
        return "pending"
    return "not_required"


def _build_enrollment_continuity(data: AdmissionsSubmitData) -> dict:
    fee_required = _application_fee_required()
    waiver_requested = bool(data.application_fee.get("waiverRequested"))
    fee_status = _application_fee_status_value(fee_required, waiver_requested)

    return {
        "phase": "admissions_to_enrollment",
        "checklist": [
            {
                "key": "application_fee",
                "title": "Application Fee",
                "status": fee_status,
                "amount": str(APPLICATION_FEE_USD),
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
                "key": "decision_and_enrollment_next_steps",
                "title": "Decision and Enrollment Next Steps",
                "status": "pending",
            },
        ],
    }


def _build_reviewer_summary(data: AdmissionsSubmitData, applicants: list[Applicant]) -> dict:
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


def _build_application_fee_status(data: AdmissionsSubmitData) -> dict:
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


def _build_payment_handoff(*, invoice_id, amount_cents: int, correlation_id: str) -> dict:
    return {
        "state": "ready",
        "requires_auth": True,
        "endpoint": "/api/finance/payments/intent/",
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


def _resolve_finance_payer_user(*, school, guardians: list[dict]):
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


def _create_application_fee_finance_records(*, school, data: AdmissionsSubmitData, application_ids: list[str], correlation_id: str) -> dict:
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

    fee_cents = int((APPLICATION_FEE_USD * 100).quantize(Decimal("1")))
    reference = f"admissions_fee:{application_ids[0] if application_ids else uuid.uuid4()}"
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
            description="Admissions Application Fee",
            due_date=timezone.localdate(),
            amount_cents=fee_cents,
            currency=APPLICATION_FEE_CURRENCY,
            reference=reference,
            academic_year_label=data.start_term,
        )

    invoice = create_invoice_from_obligations(
        school=school,
        payer_user=payer,
        period_start=timezone.localdate(),
        period_end=timezone.localdate(),
        due_date=timezone.localdate(),
        obligations=[obligation],
        created_by=None,
    )

    fee_status["finance"] = {
        "state": "invoiced",
        "payer_user_id": str(payer.id),
        "obligation_id": obligation.id,
        "invoice_id": invoice.id,
        "collection_path": "/api/finance/payments/intent/",
    }
    fee_status["payment_handoff"] = _build_payment_handoff(
        invoice_id=invoice.id,
        amount_cents=fee_cents,
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


def _build_stage_counts(apps, stage_facts: dict) -> dict:
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


def _build_conversion_rates(stage_counts: dict) -> dict:
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


def _build_velocity(events) -> dict:
    return {
        "inquiry_to_tour_completed_avg": _avg_days_between(events, "inquiry_created", "tour_completed"),
        "tour_completed_to_submitted_avg": _avg_days_between(events, "tour_completed", "application_submitted"),
        "submitted_to_decision_avg": _avg_days_between(events, "application_submitted", "decision_made"),
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


@api_view(["GET"])
@permission_classes([AllowAny])
def admissions_public_config(_request):
    return Response({"application_fee": _application_fee_config()})


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


def _resolve_school_for_submit(request, payload: dict):
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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_summary(request):
    """GET /api/v1/admissions/summary/ - Pipeline KPIs for admissions director."""
    from core.permissions import user_has_permission
    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, "admissions.view", school=school):
        return Response({"detail": "Permission denied."}, status=403)
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

    # Top sources — from Applicant.source (canonical)
    applicants = Applicant.objects.filter(school_id=school_id, application_id__in=app_ids)
    top_sources_qs = (
        applicants.values("source")
        .annotate(total=Count("id"))
        .order_by("-total", "source")[:10]
    )
    top_sources = [{"source": r["source"], "total": r["total"]} for r in top_sources_qs]

    return Response(
        {
            "academic_year": ay_name,
            "date_from": request.query_params.get("date_from"),
            "date_to": request.query_params.get("date_to"),
            "pipeline": {"total": pipeline_total, "by_stage": stage_counts},
            "conversion": conversion,
            "velocity_days": velocity,
            "top_sources": top_sources,
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def admissions_submit(request):
    """POST /api/v1/admissions/submit/ - Persist public admissions wizard submission."""
    correlation_id = _request_correlation_id(request)
    payload = request.data or {}
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
    application_ids = [str(app.id) for app in applications]
    applicant_ids = [str(applicant.id) for applicant in applicants]

    response_payload = {
        "ok": True,
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
            "next_update_target": "Within 1 business day",
            "milestones": _build_submit_milestones(),
        },
        "documents_lifecycle": _build_document_lifecycle(submit_data.documents),
        "enrollment_continuity": _build_enrollment_continuity(submit_data),
        "reviewer_summary": _build_reviewer_summary(submit_data, applicants),
        "application_fee": _create_application_fee_finance_records(
            school=school,
            data=submit_data,
            application_ids=application_ids,
            correlation_id=correlation_id,
        ),
        "fee_config": _application_fee_config(),
    }

    if idempotency_key:
        # Keep replay window short but long enough for user retries and browser retransmits.
        cache.set(
            _cache_key_for_submit(school.pk, idempotency_key),
            response_payload,
            timeout=10 * 60,
        )

    return _attach_correlation(Response(response_payload, status=201), correlation_id)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def admissions_drilldown(request):
    """GET /api/v1/admissions/drilldown/ - Paginated lead details."""
    from core.permissions import user_has_permission
    school, tenant_error = _resolve_school(request)
    if tenant_error is not None:
        return tenant_error
    if not user_has_permission(request.user, "admissions.view", school=school):
        return Response({"detail": "Permission denied."}, status=403)
    school_id = school.pk

    academic_year = request.query_params.get("academic_year")
    stage = request.query_params.get("stage")
    source = request.query_params.get("source")

    limit, offset, pagination_error = _parse_pagination(request)
    if pagination_error is not None:
        return pagination_error

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
