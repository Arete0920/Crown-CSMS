from __future__ import annotations

# pyright: reportMissingImports=false, reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

import logging
import os
from decimal import Decimal, InvalidOperation
from typing import Any, cast

from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)
ADMISSIONS_ASSESSMENT_REQUIRED = str(os.getenv("ADMISSIONS_ASSESSMENT_REQUIRED", "1")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


# ---------------------------------------------------------------------------
# Helpers  (mirrors student360 helpers so behaviour is consistent)
# ---------------------------------------------------------------------------

def _safe_decimal(x: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _compute_weighted_percent(grade_qs: Any) -> Decimal | None:
    earned = Decimal("0")
    possible = Decimal("0")
    for ge in grade_qs:
        pe = _safe_decimal(getattr(ge, "points_earned", None))
        pp = _safe_decimal(getattr(ge, "points_possible", None))
        if pp > 0:
            possible += pp
            earned += pe
    if possible <= 0:
        return None
    return (earned / possible) * Decimal("100")


def _percent_to_gpa_proxy(pct: Decimal | None) -> Decimal | None:
    if pct is None:
        return None
    for threshold, gpa in [
        (93, "4.0"), (90, "3.7"), (87, "3.3"), (83, "3.0"),
        (80, "2.7"), (77, "2.3"), (73, "2.0"), (70, "1.7"),
        (67, "1.3"), (65, "1.0"),
    ]:
        if pct >= threshold:
            return Decimal(gpa)
    return Decimal("0.0")


def _try_get_core_student(households_student: Any, school_id: Any = None) -> Any | None:
    """Bridge households.Student to core.Student for ServiceEntry FK (legacy)."""
    try:
        from core.models import Student as CoreStudent
    except Exception:
        return None

    first = getattr(households_student, "first_name", None)
    last = getattr(households_student, "last_name", None)
    if first and last:
        qs = CoreStudent.objects.filter(
            first_name__iexact=first, last_name__iexact=last
        )
        if school_id is not None:
            qs = qs.filter(school_id=str(school_id))
        cs = qs.first()
        if cs:
            return cs
    return None


def _resolve_household_for_user(user: Any) -> Any | None:
    """
    Resolve the calling user to a households.Household.

    Primary: match user.email to households.Guardian.email (Guardian has household FK).
    Demo-safe; not production-safe without a direct User to Household FK.
    """
    email = getattr(user, "email", None)
    if not email:
        return None

    try:
        from households.models import Guardian
        guardian_qs = Guardian.objects.filter(email__iexact=email)
        school_id = getattr(user, "school_id", None)
        if school_id not in (None, ""):
            guardian_qs = guardian_qs.filter(school_id=str(school_id))

        guardian = guardian_qs.select_related("household").first()
        if guardian and getattr(guardian, "household_id", None):
            return guardian.household
    except Exception:
        logger.debug("guardian email bridge unavailable", exc_info=True)

    return None


def _get_children_for_household(household: Any) -> list[Any]:
    """Return list of active households.Student for the household."""
    try:
        from households.models import Student as HHStudent
    except Exception:
        return []

    try:
        qs = HHStudent.objects.filter(household=household)
        if hasattr(HHStudent, "is_active"):
            qs = qs.filter(is_active=True)
        return list(qs.order_by("last_name", "first_name"))
    except Exception:
        return []


def _build_admissions_continuity(household: Any) -> dict[str, Any]:
    try:
        from applications.aid_projection import build_award_summary_by_household
        from applications.models import (
            Application,
            ApplicationChecklistItem,
            Applicant,
            ApplicationEvent,
            ChecklistItemStatus,
            EnrollmentContract,
        )
    except Exception:
        return {
            "available": False,
            "applications": [],
            "summary": {
                "total": 0,
                "accepted_pending_contract": 0,
                "contract_complete": 0,
                "deposit_complete": 0,
            },
        }

    school_id = getattr(household, "school_id", None)
    if not school_id:
        return {
            "available": True,
            "applications": [],
            "summary": {
                "total": 0,
                "accepted_pending_contract": 0,
                "contract_complete": 0,
                "deposit_complete": 0,
            },
        }
    return _build_admissions_continuity_payload(
        household,
        school_id,
        build_award_summary_by_household,
        Application,
        ApplicationChecklistItem,
        Applicant,
        ApplicationEvent,
        ChecklistItemStatus,
        EnrollmentContract,
    )


def _build_checklist_by_app(checklist_rows: Any, checklist_item_status: Any) -> dict[Any, dict[str, Any]]:
    checklist_by_app: dict[Any, dict[str, Any]] = {}
    for row in checklist_rows:
        app_key = row["application_id"]
        state = checklist_by_app.setdefault(
            app_key,
            {"required_total": 0, "complete_count": 0, "missing_count": 0, "pending_items": []},
        )
        state["required_total"] += 1
        if row["status"] in (
            checklist_item_status.APPROVED,
            checklist_item_status.SUBMITTED,
            checklist_item_status.UNDER_REVIEW,
        ):
            state["complete_count"] += 1
        if row["status"] in (checklist_item_status.MISSING, checklist_item_status.REJECTED):
            state["missing_count"] += 1
            state["pending_items"].append(
                {
                    "item_key": row["item_key"],
                    "title": row["title"],
                    "office": row["office"],
                    "status": row["status"],
                    "submitted_at": row["submitted_at"].isoformat() if row["submitted_at"] else None,
                }
            )
    return checklist_by_app


def _build_enrollment_state_by_app(events: Any) -> dict[Any, dict[str, Any]]:
    enrollment_state_by_app: dict[Any, dict[str, Any]] = {}
    for row in events.filter(event_type="enrollment_state_updated").order_by("application_id", "-created_at").values("application_id", "payload"):
        app_id = row["application_id"]
        if app_id not in enrollment_state_by_app:
            payload: dict[str, Any] = row.get("payload") or {}
            enrollment_state_by_app[app_id] = {
                "contract_status": payload.get("contract_status") or "not_started",
                "deposit_status": payload.get("deposit_status") or "pending",
                "note": payload.get("note") or "",
                "transition_reason": payload.get("transition_reason") or "",
            }
    return enrollment_state_by_app


def _build_decision_by_app(events: Any) -> dict[Any, str]:
    decision_by_app: dict[Any, str] = {}
    for row in events.filter(event_type="decision_made").values("application_id", "payload"):
        payload: dict[str, Any] = row.get("payload") or {}
        decision = payload.get("decision")
        if decision in ("accepted", "waitlisted", "declined"):
            decision_by_app[row["application_id"]] = decision
    return decision_by_app


def _build_admissions_continuity_payload(
    household: Any,
    school_id: Any,
    build_award_summary_by_household: Any,
    application_model: Any,
    application_checklist_item_model: Any,
    applicant_model: Any,
    application_event_model: Any,
    checklist_item_status: Any,
    enrollment_contract_model: Any,
) -> dict[str, Any]:
    apps = list(application_model.objects.filter(school_id=school_id, household=household).order_by("-created_at"))
    app_ids = [app.id for app in apps]
    events = application_event_model.objects.filter(school_id=school_id, application_id__in=app_ids)
    awards_by_household = build_award_summary_by_household(
        school_id=school_id,
        household_ids=[app.household_id for app in apps if getattr(app, "household_id", None)],
    )
    latest_contract_by_app = {
        row.application_id: row
        for row in enrollment_contract_model.objects.filter(school_id=school_id, application_id__in=app_ids).order_by(
            "application_id", "-version", "-created_at"
        )
    }
    applicants_by_app: dict[Any, dict[str, Any]] = {
        row["application_id"]: row["flags"] or {}
        for row in applicant_model.objects.filter(school_id=school_id, application_id__in=app_ids)
        .order_by("application_id", "created_at")
        .values("application_id", "flags")
    }
    checklist_by_app = _build_checklist_by_app(
        application_checklist_item_model.objects.filter(school_id=school_id, application_id__in=app_ids).values(
            "application_id", "item_key", "title", "office", "status", "submitted_at"
        ),
        checklist_item_status,
    )
    decision_by_app = _build_decision_by_app(events)
    enrolled_ids = set(events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True))
    enrollment_state_by_app = _build_enrollment_state_by_app(events)

    applications_payload: list[dict[str, Any]] = []
    accepted_pending_contract = 0
    contract_complete = 0
    deposit_complete = 0

    for app in apps:
        row, pending_contract, completed_contract, completed_deposit = _build_admissions_application_row(
            app,
            decision_by_app.get(app.id),
            enrolled_ids,
            enrollment_state_by_app,
            checklist_by_app,
            applicants_by_app,
            latest_contract_by_app,
            awards_by_household,
            events,
        )
        applications_payload.append(row)
        accepted_pending_contract += int(pending_contract)
        contract_complete += int(completed_contract)
        deposit_complete += int(completed_deposit)

    return {
        "available": True,
        "applications": applications_payload,
        "summary": {
            "total": len(applications_payload),
            "accepted_pending_contract": accepted_pending_contract,
            "contract_complete": contract_complete,
            "deposit_complete": deposit_complete,
        },
    }


def _admissions_lifecycle_stage(app: Any, decision: str | None, enrolled_ids: set[Any]) -> str:
    if app.id in enrolled_ids:
        return "enrolled"
    if decision == "accepted":
        return "accepted"
    if decision == "waitlisted":
        return "waitlisted"
    if decision == "declined":
        return "declined"
    if app.status == "IN_REVIEW":
        return "in_review"
    if app.status == "SUBMITTED":
        return "application_submitted"
    return "application_started"


def _admissions_financial_aid_status(flags: dict[str, Any]) -> str:
    financial_aid_interest = flags.get("financial_aid_interest")
    intent = ""
    if isinstance(financial_aid_interest, dict):
        financial_aid_interest_map = cast(dict[str, Any], financial_aid_interest)
        intent = str(financial_aid_interest_map.get("intent") or "")
    return {
        "applying": "Aid Application Started",
        "not_applying": "Not Applying",
        "undecided": "Aid Interest Indicated",
    }.get(intent, "Aid Interest Indicated")


def _admissions_contract_and_deposit_status(state: dict[str, Any], lifecycle_stage: str) -> tuple[str, str]:
    if lifecycle_stage in ("accepted", "enrolled"):
        return state.get("contract_status") or "not_started", state.get("deposit_status") or "pending"
    return "not_applicable", "not_applicable"


def _admissions_status_labels(lifecycle_stage: str) -> tuple[str, str]:
    mapping = {
        "in_review": ("Under Review", "Admissions team is reviewing your file. Watch for checklist requests."),
        "application_submitted": ("Application Submitted", "Complete remaining checklist items to move to Ready for Review."),
        "accepted": ("Accepted", "Complete enrollment contract and deposit."),
        "waitlisted": ("Waitlisted", "Waitlist Status / Next Update"),
        "declined": ("Declined", "Contact admissions for future-cycle guidance if needed."),
        "enrolled": ("Enrollment Complete", "Complete classroom readiness and portal activation steps."),
    }
    return mapping.get(lifecycle_stage, ("Application Started", "Continue and submit your application."))


def _admissions_assessment_context(flags: dict[str, Any]) -> tuple[bool, str, str, str, str]:
    preferred_tour_window = str(flags.get("preferred_tour_window") or "").strip()
    preferred_interview_mode = str(flags.get("preferred_interview_mode") or "").strip()
    assessment_preferences_captured = bool(preferred_tour_window and preferred_interview_mode)
    if assessment_preferences_captured:
        return True, preferred_tour_window, preferred_interview_mode, "scheduling_in_progress", "Admissions team will confirm your assessment/interview slot."
    if ADMISSIONS_ASSESSMENT_REQUIRED:
        return False, preferred_tour_window, preferred_interview_mode, "required", "Add preferred tour/interview options to continue scheduling."
    return False, preferred_tour_window, preferred_interview_mode, "optional", "Assessment scheduling preferences can be submitted later."


def _admissions_deadline(app: Any, lifecycle_stage: str) -> str | None:
    if app.submitted_at and lifecycle_stage in ("application_submitted", "in_review"):
        return (app.submitted_at + timezone.timedelta(days=2)).isoformat()
    if app.submitted_at and lifecycle_stage == "accepted":
        return (app.submitted_at + timezone.timedelta(days=7)).isoformat()
    return None


def _admissions_sla(app: Any, lifecycle_stage: str) -> tuple[str | None, int | None]:
    submitted_or_updated = app.submitted_at or app.updated_at or app.created_at
    if not submitted_or_updated:
        return None, None
    sla = _workflow_sla_for_stage(lifecycle_stage)
    due_at_dt = submitted_or_updated + timezone.timedelta(hours=sla["target_hours"])
    return due_at_dt.isoformat(), int((due_at_dt - timezone.now()).total_seconds() // 60)


def _admissions_readiness_score(checklist: dict[str, Any]) -> tuple[int, int, int, bool]:
    checklist_total = int(checklist.get("required_total", 0) or 0)
    checklist_missing = int(checklist.get("missing_count", 0) or 0)
    blocked_checklist = checklist_missing > 0
    if checklist_total <= 0:
        return 0, checklist_total, checklist_missing, blocked_checklist
    score = int(max(0, min(100, round(((checklist_total - checklist_missing) / checklist_total) * 100))))
    return score, checklist_total, checklist_missing, blocked_checklist


def _admissions_sync_statuses(aid_award_count: int, lifecycle_stage: str) -> tuple[str, str]:
    if aid_award_count > 0 and lifecycle_stage in ("accepted", "enrolled"):
        return "ready_for_contract_adjustment", "ready_for_billing_application"
    if aid_award_count > 0:
        return "pending_acceptance", "pending_acceptance"
    return "not_synced", "not_synced"


def _get_household_balance_cents(household: Any, invoice_model: Any, invoice_line_model: Any) -> int:
    if invoice_model is None or not hasattr(invoice_model, "household"):
        return 0

    try:
        inv_qs = invoice_model.objects.filter(household=household)
        if hasattr(invoice_model, "status"):
            inv_qs = inv_qs.filter(status__in=["open", "unpaid", "pending"])
        elif hasattr(invoice_model, "is_paid"):
            inv_qs = inv_qs.filter(is_paid=False)

        if invoice_line_model is not None and hasattr(invoice_line_model, "invoice"):
            lines_total = invoice_line_model.objects.filter(invoice__in=inv_qs).aggregate(
                total=Coalesce(Sum("amount"), Decimal("0"))
            )["total"]
            return int((_safe_decimal(lines_total) * Decimal("100")).quantize(Decimal("1")))

        if hasattr(invoice_model, "amount_due"):
            raw = inv_qs.aggregate(total=Coalesce(Sum("amount_due"), Decimal("0")))["total"]
            return int((_safe_decimal(raw) * Decimal("100")).quantize(Decimal("1")))
    except Exception:
        logger.debug("household balance unavailable", exc_info=True)

    return 0


def _build_child_grade_summary(
    student: Any,
    grade_entry_model: Any,
    assignment_model: Any,
    enrollment_model: Any,
    school_id: Any,
    now: Any,
    seven_days: Any,
) -> tuple[dict[str, Any], int, int]:
    summary: dict[str, Any] = {
        "current_average": None,
        "gpa": None,
        "missing_assignments": 0,
        "upcoming_assignments": [],
    }
    missing_total = 0
    upcoming_total = 0

    if grade_entry_model is None or assignment_model is None:
        return summary, missing_total, upcoming_total

    try:
        ge_qs = grade_entry_model.objects.filter(student=student).select_related("assignment")
        pct = _compute_weighted_percent(ge_qs)
        if pct is not None:
            summary["current_average"] = float(pct.quantize(Decimal("0.1")))
            gpa = _percent_to_gpa_proxy(pct)
            summary["gpa"] = float(gpa) if gpa is not None else None

        asgn_filter: dict[str, Any] = {"is_published": True, "due_date__lt": now}
        if school_id:
            asgn_filter["school_id"] = school_id

        has_enrollment_scope = False
        if enrollment_model is not None:
            section_ids = list(enrollment_model.objects.filter(student=student).values_list("section_id", flat=True))
            if section_ids:
                asgn_filter["section_id__in"] = section_ids
                has_enrollment_scope = True
            else:
                return summary, missing_total, upcoming_total

        past_due_qs = assignment_model.objects.filter(**asgn_filter)
        entered_ids = set(ge_qs.exclude(assignment=None).values_list("assignment_id", flat=True))
        missing_no_entry = past_due_qs.exclude(id__in=entered_ids).count()
        missing_blank = ge_qs.filter(
            assignment__is_published=True,
            assignment__due_date__lt=now,
        ).filter(Q(points_earned__isnull=True) | Q(points_possible__isnull=True)).count()
        summary["missing_assignments"] = int(missing_no_entry + missing_blank)

        up_filter: dict[str, Any] = {"is_published": True, "due_date__gte": now, "due_date__lte": seven_days}
        if school_id:
            up_filter["school_id"] = school_id
        if has_enrollment_scope and "section_id__in" in asgn_filter:
            up_filter["section_id__in"] = asgn_filter["section_id__in"]

        summary["upcoming_assignments"] = _serialize_upcoming_assignments(
            assignment_model.objects.filter(**up_filter).order_by("due_date", "id")[:10]
        )
        missing_total = summary["missing_assignments"]
        upcoming_total = len(summary["upcoming_assignments"])
    except Exception:
        logger.debug("optional assignment data unavailable for child", exc_info=True)

    return summary, missing_total, upcoming_total


def _serialize_upcoming_assignments(assignments: Any) -> list[dict[str, Any]]:
    return [
        {
            "id": str(a.id),
            "name": a.name,
            "due_date": a.due_date.isoformat() if a.due_date else None,
            "points_possible": float(_safe_decimal(a.points_possible)) if a.points_possible is not None else None,
        }
        for a in assignments
    ]


def _build_child_service_hours_summary(student: Any, service_entry_model: Any, school_id: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"available": False, "completed": 0, "required": 30}
    if service_entry_model is None:
        return summary

    try:
        core_student = _try_get_core_student(student, school_id=school_id)
        if core_student:
            approved = service_entry_model.objects.filter(student=core_student, status="approved")
            total_h = approved.aggregate(total=Coalesce(Sum("hours"), Decimal("0")))["total"]
            summary = {
                "available": True,
                "completed": float(_safe_decimal(total_h).quantize(Decimal("0.1"))),
                "required": 30,
            }
    except Exception:
        logger.debug("optional service hours unavailable for child", exc_info=True)

    return summary


def _build_child_financial_summary(student: Any, invoice_model: Any, invoice_line_model: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"available": False, "balance_cents": 0}
    if invoice_line_model is None or invoice_model is None:
        return summary

    try:
        lines = invoice_line_model.objects.filter(student=student).select_related("invoice")
        inv_filter = Q()
        if hasattr(invoice_model, "status"):
            inv_filter = Q(invoice__status__in=["open", "unpaid", "pending"])
        elif hasattr(invoice_model, "is_paid"):
            inv_filter = Q(invoice__is_paid=False)

        if inv_filter:
            lines = lines.filter(inv_filter)

        total_amount = lines.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
        summary = {
            "available": True,
            "balance_cents": int((_safe_decimal(total_amount) * Decimal("100")).quantize(Decimal("1"))),
        }
    except Exception:
        logger.debug("optional finance data unavailable for child", exc_info=True)

    return summary


def _build_child_alerts(child_row: dict[str, Any]) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    if child_row["current_average"] is not None and child_row["current_average"] < 75:
        alerts.append({
            "type": "academic",
            "severity": "warning",
            "message": f"{child_row['first_name']} has an average below 75%.",
        })
    if child_row["missing_assignments"] >= 3:
        alerts.append({
            "type": "work",
            "severity": "warning",
            "message": f"{child_row['first_name']} has 3+ missing assignments.",
        })
    return alerts


def _build_child_overview_row(
    student: Any,
    grade_entry_model: Any,
    assignment_model: Any,
    enrollment_model: Any,
    invoice_model: Any,
    invoice_line_model: Any,
    service_entry_model: Any,
    school_id: Any,
    now: Any,
    seven_days: Any,
) -> tuple[dict[str, Any], int, int]:
    row: dict[str, Any] = {
        "id": str(getattr(student, "id")),
        "first_name": getattr(student, "first_name", ""),
        "last_name": getattr(student, "last_name", ""),
        "grade_level": getattr(student, "grade_level", ""),
        "current_average": None,
        "gpa": None,
        "missing_assignments": 0,
        "upcoming_assignments": [],
        "service_hours": {"available": False, "completed": 0, "required": 30},
        "financial": {"available": False, "balance_cents": 0},
        "alerts": [],
    }

    grade_summary, missing_total, upcoming_total = _build_child_grade_summary(
        student,
        grade_entry_model,
        assignment_model,
        enrollment_model,
        school_id,
        now,
        seven_days,
    )
    row.update(grade_summary)
    row["service_hours"] = _build_child_service_hours_summary(student, service_entry_model, school_id)
    row["financial"] = _build_child_financial_summary(student, invoice_model, invoice_line_model)
    row["alerts"] = _build_child_alerts(row)
    return row, missing_total, upcoming_total


def _serialize_admissions_contract(contract: Any) -> dict[str, Any]:
    totals = contract.contract_totals if isinstance(contract.contract_totals, dict) else {}
    return {
        "contract_id": str(contract.id),
        "version": contract.version,
        "status": contract.status,
        "line_items": contract.line_items or [],
        "totals": {
            key: int(totals.get(key) or 0)
            for key in (
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
        },
        "payment_plan": contract.payment_plan,
        "payment_schedule": contract.payment_schedule,
        "responsible_payer": contract.responsible_payer,
        "refund_terms": contract.refund_terms,
        "issued_at": contract.issued_at.isoformat() if contract.issued_at else None,
        "signed_at": contract.signed_at.isoformat() if contract.signed_at else None,
        "countersigned_at": contract.countersigned_at.isoformat() if contract.countersigned_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
    }


def _workflow_sla_for_stage(stage: str) -> dict[str, Any]:
    stage_hours = {
        "application_submitted": 24,
        "in_review": 24,
        "accepted": 48,
        "waitlisted": 120,
        "application_started": 72,
        "enrolled": 24,
    }
    hours = int(stage_hours.get(stage, 72))
    return {"target_hours": hours, "target_label": f"{hours}h target"}


def _build_communications_timeline(app_id: Any, events_qs: Any) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for row in (
        events_qs.filter(
            application_id=app_id,
            event_type__in=[
                "application_submitted",
                "decision_made",
                "enrollment_state_updated",
                "enrollment_confirmed",
            ],
        )
        .order_by("-created_at")
        .values("event_type", "created_at", "payload")[:12]
    ):
        payload = row.get("payload") or {}
        timeline.append(
            {
                "when": row["created_at"].isoformat() if row.get("created_at") else None,
                "event_type": row["event_type"],
                "title": row["event_type"].replace("_", " ").title(),
                "detail": payload.get("note") or payload.get("transition_reason") or "Status update recorded.",
            }
        )
    return timeline


def _build_admissions_application_row(
    app: Any,
    decision: str | None,
    enrolled_ids: set[Any],
    enrollment_state_by_app: dict[Any, dict[str, Any]],
    checklist_by_app: dict[Any, dict[str, Any]],
    applicants_by_app: dict[Any, dict[str, Any]],
    latest_contract_by_app: dict[Any, Any],
    awards_by_household: dict[Any, dict[str, Any]],
    events: Any,
) -> tuple[dict[str, Any], bool, bool, bool]:
    lifecycle_stage = _admissions_lifecycle_stage(app, decision, enrolled_ids)
    state = enrollment_state_by_app.get(app.id, {})
    checklist = checklist_by_app.get(app.id, {"required_total": 0, "complete_count": 0, "missing_count": 0, "pending_items": []})
    flags = applicants_by_app.get(app.id) or {}
    latest_contract = latest_contract_by_app.get(app.id)
    award_summary = awards_by_household.get(app.household_id, {"count": 0, "total": "0"})
    aid_award_count = int(award_summary.get("count") or 0)
    financial_aid_status = _admissions_financial_aid_status(flags)
    contract_status, deposit_status = _admissions_contract_and_deposit_status(state, lifecycle_stage)
    aid_contract_sync_status, aid_billing_sync_status = _admissions_sync_statuses(aid_award_count, lifecycle_stage)
    sla = _workflow_sla_for_stage(lifecycle_stage)
    applicant_to_student_status = {"enrolled": "completed", "accepted": "ready"}.get(lifecycle_stage, "pending")
    classroom_readiness_status = {"enrolled": "in_progress", "accepted": "pending"}.get(lifecycle_stage, "pending")
    parent_portal_activation_status = {"enrolled": "in_progress", "accepted": "pending"}.get(lifecycle_stage, "pending")
    parent_status, next_action = _admissions_status_labels(lifecycle_stage)
    assessment_captured, preferred_tour_window, preferred_interview_mode, assessment_status, assessment_next_action = _admissions_assessment_context(flags)
    deadline_at = _admissions_deadline(app, lifecycle_stage)
    sla_due_at, sla_remaining_minutes = _admissions_sla(app, lifecycle_stage)
    readiness_score, checklist_total, checklist_missing, blocked_checklist = _admissions_readiness_score(checklist)

    row = {
        "application_id": str(app.id),
        "application_status": app.status,
        "lifecycle_stage": lifecycle_stage,
        "parent_status": parent_status,
        "next_action": next_action,
        "deadline_at": deadline_at,
        "workflow_sla": {
            "target_hours": sla["target_hours"],
            "target_label": sla["target_label"],
            "due_at": sla_due_at,
            "remaining_minutes": sla_remaining_minutes,
        },
        "review_owner": "Admissions Team",
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "contract_status": contract_status,
        "contract_detail": _serialize_admissions_contract(latest_contract) if latest_contract else None,
        "deposit_status": deposit_status,
        "transition_reason": state.get("transition_reason") or "",
        "financial_aid_status": financial_aid_status,
        "aid_award_count": aid_award_count,
        "aid_contract_sync_status": aid_contract_sync_status,
        "aid_billing_sync_status": aid_billing_sync_status,
        "applicant_to_student_status": applicant_to_student_status,
        "classroom_readiness_status": classroom_readiness_status,
        "parent_portal_activation_status": parent_portal_activation_status,
        "assessment_interview": {
            "required": ADMISSIONS_ASSESSMENT_REQUIRED,
            "status": assessment_status,
            "preferred_tour_window": preferred_tour_window,
            "preferred_interview_mode": preferred_interview_mode,
            "next_action": assessment_next_action,
            "target_sla": "Within 3-5 business days",
        },
        "checklist_summary": {
            "required_total": checklist_total,
            "complete_count": int(checklist.get("complete_count", 0) or 0),
            "missing_count": checklist_missing,
        },
        "checklist_pending_items": checklist.get("pending_items") or [],
        "journey_health": {
            "status": "in_progress" if assessment_captured or not blocked_checklist else "attention_needed",
            "blocked": blocked_checklist,
            "blocking_reason": "Checklist items still missing." if blocked_checklist else "",
            "sla_remaining_minutes": sla_remaining_minutes,
            "sla_due_at": sla_due_at,
        },
        "decision_packet_readiness": {
            "score": readiness_score,
            "status": "ready" if readiness_score >= 90 else "in_progress",
            "missing_count": checklist_missing,
            "required_total": checklist_total,
        },
        "payment_precheck": {
            "contract_ready": contract_status in ("signed", "countersigned"),
            "deposit_ready": deposit_status in ("invoiced", "paid", "waived"),
            "billing_method_ready": lifecycle_stage in ("accepted", "enrolled"),
            "status": "ready" if lifecycle_stage in ("accepted", "enrolled") else "pending",
        },
        "household_communications_timeline": _build_communications_timeline(app.id, events),
    }

    accepted_pending_contract = lifecycle_stage == "accepted" and contract_status != "countersigned"
    contract_complete = contract_status == "countersigned"
    deposit_complete = deposit_status in ("paid", "waived")
    return row, accepted_pending_contract, contract_complete, deposit_complete


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class ParentSelfOverview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: Any):
        user = request.user

        household = _resolve_household_for_user(user)
        if not household:
            return Response(
                {
                    "detail": (
                        "No household found for current user. "
                        "(Demo bridge: Guardian email match failed - contact school admin.)"
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        children = _get_children_for_household(household)

        # Optional model imports - degrade gracefully if any app is missing.
        grade_entry_model = None
        assignment_model = None
        enrollment_model = None
        invoice_model = None
        invoice_line_model = None
        service_entry_model = None

        try:
            from gradebook.models import GradeEntry as grade_entry_model
            from academics.models import Assignment as assignment_model, Enrollment as enrollment_model
        except Exception:
            logger.debug("gradebook/academics optional imports unavailable", exc_info=True)

        try:
            from billing.models import Invoice as invoice_model, InvoiceLine as invoice_line_model
        except Exception:
            logger.debug("billing optional imports unavailable", exc_info=True)

        try:
            from servicehours.models import ServiceEntry as service_entry_model
        except Exception:
            logger.debug("servicehours optional imports unavailable", exc_info=True)

        now = timezone.now().date()
        seven_days = now + timezone.timedelta(days=7)
        household_balance_cents = _get_household_balance_cents(household, invoice_model, invoice_line_model)

        child_rows = []
        missing_total = 0
        upcoming_total = 0

        for student in children:
            school_id = getattr(student, "school_id", None)
            row, missing_delta, upcoming_delta = _build_child_overview_row(
                student,
                grade_entry_model,
                assignment_model,
                enrollment_model,
                invoice_model,
                invoice_line_model,
                service_entry_model,
                school_id,
                now,
                seven_days,
            )
            child_rows.append(row)
            missing_total += missing_delta
            upcoming_total += upcoming_delta

        payload = {
            "household": {
                "id": str(getattr(household, "id")),
                "name": getattr(household, "name", ""),
                "balance_cents": household_balance_cents,
            },
            "children_count": len(child_rows),
            "missing_assignments_total": missing_total,
            "upcoming_assignments_total": upcoming_total,
            "children": child_rows,
            "admissions_continuity": _build_admissions_continuity(household),
        }

        return Response(payload, status=status.HTTP_200_OK)







