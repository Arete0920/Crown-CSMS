from __future__ import annotations

import logging
import os
from decimal import Decimal, InvalidOperation

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

def _safe_decimal(x, default=Decimal("0")):
    try:
        return Decimal(str(x))
    except (InvalidOperation, TypeError, ValueError):
        return default


def _compute_weighted_percent(grade_qs):
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


def _percent_to_gpa_proxy(pct):
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


def _try_get_core_student(households_student, school_id=None):
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


def _resolve_household_for_user(user):
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


def _get_children_for_household(household):
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


def _build_admissions_continuity(household):
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

    def serialize_contract(contract):
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

    def workflow_sla_for_stage(stage: str) -> dict:
        stage_hours = {
            "application_submitted": 24,
            "in_review": 24,
            "accepted": 48,
            "waitlisted": 120,
            "application_started": 72,
            "enrolled": 24,
        }
        hours = int(stage_hours.get(stage, 72))
        return {
            "target_hours": hours,
            "target_label": f"{hours}h target",
        }

    def build_communications_timeline(app_id, events_qs):
        timeline = []
        for row in (
            events_qs.filter(application_id=app_id, event_type__in=[
                "application_submitted",
                "decision_made",
                "enrollment_state_updated",
                "enrollment_confirmed",
            ])
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

    apps = list(
        Application.objects.filter(school_id=school_id, household=household).order_by("-created_at")
    )
    app_ids = [a.id for a in apps]
    events = ApplicationEvent.objects.filter(school_id=school_id, application_id__in=app_ids)
    household_ids = [a.household_id for a in apps if getattr(a, "household_id", None)]
    awards_by_household = build_award_summary_by_household(school_id=school_id, household_ids=household_ids)
    latest_contract_by_app = {
        row.application_id: row
        for row in EnrollmentContract.objects.filter(school_id=school_id, application_id__in=app_ids).order_by(
            "application_id", "-version", "-created_at"
        )
    }
    applicants_by_app = {
        row["application_id"]: row["flags"] or {}
        for row in Applicant.objects.filter(school_id=school_id, application_id__in=app_ids)
        .order_by("application_id", "created_at")
        .values("application_id", "flags")
    }

    checklist_rows = list(
        ApplicationChecklistItem.objects.filter(school_id=school_id, application_id__in=app_ids)
        .values("application_id", "item_key", "title", "office", "status", "submitted_at")
    )
    checklist_by_app = {}
    for row in checklist_rows:
        app_key = row["application_id"]
        state = checklist_by_app.setdefault(
            app_key,
            {"required_total": 0, "complete_count": 0, "missing_count": 0, "pending_items": []},
        )
        state["required_total"] += 1
        if row["status"] in (ChecklistItemStatus.APPROVED, ChecklistItemStatus.SUBMITTED, ChecklistItemStatus.UNDER_REVIEW):
            state["complete_count"] += 1
        if row["status"] in (ChecklistItemStatus.MISSING, ChecklistItemStatus.REJECTED):
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

    decision_by_app = {}
    for row in events.filter(event_type="decision_made").values("application_id", "payload"):
        decision = (row.get("payload") or {}).get("decision")
        if decision in ("accepted", "waitlisted", "declined"):
            decision_by_app[row["application_id"]] = decision

    enrolled_ids = set(events.filter(event_type="enrollment_confirmed").values_list("application_id", flat=True))
    enrollment_state_by_app = {}
    for row in (
        events.filter(event_type="enrollment_state_updated")
        .order_by("application_id", "-created_at")
        .values("application_id", "payload")
    ):
        app_id = row["application_id"]
        if app_id in enrollment_state_by_app:
            continue
        payload = row.get("payload") or {}
        enrollment_state_by_app[app_id] = {
            "contract_status": payload.get("contract_status") or "not_started",
            "deposit_status": payload.get("deposit_status") or "pending",
            "note": payload.get("note") or "",
            "transition_reason": payload.get("transition_reason") or "",
        }

    applications_payload = []
    accepted_pending_contract = 0
    contract_complete = 0
    deposit_complete = 0

    for app in apps:
        decision = decision_by_app.get(app.id)
        if app.id in enrolled_ids:
            lifecycle_stage = "enrolled"
        elif decision == "accepted":
            lifecycle_stage = "accepted"
        elif decision == "waitlisted":
            lifecycle_stage = "waitlisted"
        elif decision == "declined":
            lifecycle_stage = "declined"
        elif app.status == "IN_REVIEW":
            lifecycle_stage = "in_review"
        elif app.status == "SUBMITTED":
            lifecycle_stage = "application_submitted"
        else:
            lifecycle_stage = "application_started"

        state = enrollment_state_by_app.get(app.id, {})
        checklist = checklist_by_app.get(app.id, {"required_total": 0, "complete_count": 0, "missing_count": 0, "pending_items": []})
        flags = applicants_by_app.get(app.id) or {}
        latest_contract = latest_contract_by_app.get(app.id)
        award_summary = awards_by_household.get(app.household_id, {"count": 0, "total": "0"})
        aid_award_count = int(award_summary.get("count") or 0)
        financial_aid_intent = (flags.get("financial_aid_interest") or {}).get("intent")
        preferred_tour_window = str(flags.get("preferred_tour_window") or "").strip()
        preferred_interview_mode = str(flags.get("preferred_interview_mode") or "").strip()
        assessment_preferences_captured = bool(preferred_tour_window and preferred_interview_mode)
        if financial_aid_intent == "applying":
            financial_aid_status = "Aid Application Started"
        elif financial_aid_intent == "not_applying":
            financial_aid_status = "Not Applying"
        elif financial_aid_intent == "undecided":
            financial_aid_status = "Aid Interest Indicated"
        else:
            financial_aid_status = "Aid Interest Indicated"

        if lifecycle_stage in ("accepted", "enrolled"):
            contract_status = state.get("contract_status") or "not_started"
            deposit_status = state.get("deposit_status") or "pending"
        else:
            contract_status = "not_applicable"
            deposit_status = "not_applicable"

        if aid_award_count > 0 and lifecycle_stage in ("accepted", "enrolled"):
            aid_contract_sync_status = "ready_for_contract_adjustment"
            aid_billing_sync_status = "ready_for_billing_application"
        elif aid_award_count > 0:
            aid_contract_sync_status = "pending_acceptance"
            aid_billing_sync_status = "pending_acceptance"
        else:
            aid_contract_sync_status = "not_synced"
            aid_billing_sync_status = "not_synced"

        if lifecycle_stage == "enrolled":
            applicant_to_student_status = "completed"
            classroom_readiness_status = "in_progress"
            parent_portal_activation_status = "in_progress"
        elif lifecycle_stage == "accepted":
            applicant_to_student_status = "ready"
            classroom_readiness_status = "pending"
            parent_portal_activation_status = "pending"
        else:
            applicant_to_student_status = "pending"
            classroom_readiness_status = "pending"
            parent_portal_activation_status = "pending"

        if lifecycle_stage == "in_review":
            parent_status = "Under Review"
            next_action = "Admissions team is reviewing your file. Watch for checklist requests."
        elif lifecycle_stage == "application_submitted":
            parent_status = "Application Submitted"
            next_action = "Complete remaining checklist items to move to Ready for Review."
        elif lifecycle_stage == "accepted":
            parent_status = "Accepted"
            next_action = "Complete enrollment contract and deposit."
        elif lifecycle_stage == "waitlisted":
            parent_status = "Waitlisted"
            next_action = "Waitlist Status / Next Update"
        elif lifecycle_stage == "declined":
            parent_status = "Declined"
            next_action = "Contact admissions for future-cycle guidance if needed."
        elif lifecycle_stage == "enrolled":
            parent_status = "Enrollment Complete"
            next_action = "Complete classroom readiness and portal activation steps."
        else:
            parent_status = "Application Started"
            next_action = "Continue and submit your application."

        if assessment_preferences_captured:
            assessment_status = "scheduling_in_progress"
            assessment_next_action = "Admissions team will confirm your assessment/interview slot."
        elif ADMISSIONS_ASSESSMENT_REQUIRED:
            assessment_status = "required"
            assessment_next_action = "Add preferred tour/interview options to continue scheduling."
        else:
            assessment_status = "optional"
            assessment_next_action = "Assessment scheduling preferences can be submitted later."

        deadline_at = None
        if app.submitted_at and lifecycle_stage in ("application_submitted", "in_review"):
            deadline_at = (app.submitted_at + timezone.timedelta(days=2)).isoformat()
        elif app.submitted_at and lifecycle_stage == "accepted":
            deadline_at = (app.submitted_at + timezone.timedelta(days=7)).isoformat()

        sla = workflow_sla_for_stage(lifecycle_stage)
        submitted_or_updated = app.submitted_at or app.updated_at or app.created_at
        sla_due_at = None
        sla_remaining_minutes = None
        if submitted_or_updated:
            due_at_dt = submitted_or_updated + timezone.timedelta(hours=sla["target_hours"])
            sla_due_at = due_at_dt.isoformat()
            remaining_minutes = int((due_at_dt - timezone.now()).total_seconds() // 60)
            sla_remaining_minutes = remaining_minutes

        checklist_total = int(checklist.get("required_total", 0) or 0)
        checklist_missing = int(checklist.get("missing_count", 0) or 0)
        blocked_checklist = checklist_missing > 0
        readiness_score = 0
        if checklist_total > 0:
            readiness_score = int(max(0, min(100, round(((checklist_total - checklist_missing) / checklist_total) * 100))))

        decision_packet_readiness = {
            "score": readiness_score,
            "status": "ready" if readiness_score >= 90 else "in_progress",
            "missing_count": checklist_missing,
            "required_total": checklist_total,
        }

        payment_precheck = {
            "contract_ready": contract_status in ("signed", "countersigned"),
            "deposit_ready": deposit_status in ("invoiced", "paid", "waived"),
            "billing_method_ready": lifecycle_stage in ("accepted", "enrolled"),
            "status": "ready" if lifecycle_stage in ("accepted", "enrolled") else "pending",
        }
        health_status = "in_progress"
        if lifecycle_stage in ("accepted", "enrolled") and not blocked_checklist:
            health_status = "on_track"
        elif blocked_checklist:
            health_status = "attention_needed"

        journey_health = {
            "status": health_status,
            "blocked": blocked_checklist,
            "blocking_reason": "Checklist items still missing." if blocked_checklist else "",
            "sla_remaining_minutes": sla_remaining_minutes,
            "sla_due_at": sla_due_at,
        }

        if lifecycle_stage == "accepted" and contract_status != "countersigned":
            accepted_pending_contract += 1
        if contract_status == "countersigned":
            contract_complete += 1
        if deposit_status in ("paid", "waived"):
            deposit_complete += 1

        applications_payload.append(
            {
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
                "contract_detail": serialize_contract(latest_contract) if latest_contract else None,
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
                "journey_health": journey_health,
                "decision_packet_readiness": decision_packet_readiness,
                "payment_precheck": payment_precheck,
                "household_communications_timeline": build_communications_timeline(app.id, events),
            }
        )

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


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

class ParentSelfOverview(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
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

        # Household balance (open invoices, if invoice model is household-scoped)
        household_balance_cents = 0
        if invoice_model is not None and hasattr(invoice_model, "household"):
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
                    household_balance_cents = int(
                        (_safe_decimal(lines_total) * Decimal("100")).quantize(Decimal("1"))
                    )
                elif hasattr(invoice_model, "amount_due"):
                    raw = inv_qs.aggregate(total=Coalesce(Sum("amount_due"), Decimal("0")))["total"]
                    household_balance_cents = int(
                        (_safe_decimal(raw) * Decimal("100")).quantize(Decimal("1"))
                    )
            except Exception:
                logger.debug("household balance unavailable", exc_info=True)

        # Per-child blocks
        child_rows = []
        missing_total = 0
        upcoming_total = 0

        for s in children:
            school_id = getattr(s, "school_id", None)

            row = {
                "id": str(getattr(s, "id")),
                "first_name": getattr(s, "first_name", ""),
                "last_name": getattr(s, "last_name", ""),
                "grade_level": getattr(s, "grade_level", ""),
                "current_average": None,
                "gpa": None,
                "missing_assignments": 0,
                "upcoming_assignments": [],
                "service_hours": {"available": False, "completed": 0, "required": 30},
                "financial": {"available": False, "balance_cents": 0},
                "alerts": [],
            }

            # Grades
            if grade_entry_model is not None and assignment_model is not None:
                try:
                    ge_qs = grade_entry_model.objects.filter(student=s).select_related("assignment")
                    pct = _compute_weighted_percent(ge_qs)
                    if pct is not None:
                        row["current_average"] = float(pct.quantize(Decimal("0.1")))
                        gpa = _percent_to_gpa_proxy(pct)
                        row["gpa"] = float(gpa) if gpa is not None else None

                    # Missing assignments: published + past-due + no entry or blank entry
                    asgn_filter = {"is_published": True, "due_date__lt": now}
                    if school_id:
                        asgn_filter["school_id"] = school_id

                    # Scope assignment visibility to the student's enrolled sections when available.
                    has_enrollment_scope = False
                    if enrollment_model is not None:
                        section_ids = list(
                            enrollment_model.objects.filter(student=s).values_list("section_id", flat=True)
                        )
                        if section_ids:
                            asgn_filter["section_id__in"] = section_ids
                            has_enrollment_scope = True
                        else:
                            # If enrollments exist in schema but none are linked for this student,
                            # do not fall back to school-wide assignment visibility.
                            row["missing_assignments"] = 0
                            row["upcoming_assignments"] = []
                            missing_total += 0
                            upcoming_total += 0
                            continue

                    past_due_qs = assignment_model.objects.filter(**asgn_filter)
                    entered_ids = set(
                        ge_qs.exclude(assignment=None).values_list("assignment_id", flat=True)
                    )

                    missing_no_entry = past_due_qs.exclude(id__in=entered_ids).count()
                    missing_blank = ge_qs.filter(
                        assignment__is_published=True,
                        assignment__due_date__lt=now,
                    ).filter(
                        Q(points_earned__isnull=True) | Q(points_possible__isnull=True)
                    ).count()

                    row["missing_assignments"] = int(missing_no_entry + missing_blank)

                    # Upcoming assignments: next 7 days
                    up_filter = {"is_published": True, "due_date__gte": now, "due_date__lte": seven_days}
                    if school_id:
                        up_filter["school_id"] = school_id
                    if has_enrollment_scope and "section_id__in" in asgn_filter:
                        up_filter["section_id__in"] = asgn_filter["section_id__in"]

                    upcoming = assignment_model.objects.filter(**up_filter).order_by("due_date", "id")[:10]
                    row["upcoming_assignments"] = [
                        {
                            "id": str(a.id),
                            "name": a.name,
                            "due_date": a.due_date.isoformat() if a.due_date else None,
                            "points_possible": (
                                float(_safe_decimal(a.points_possible))
                                if a.points_possible is not None else None
                            ),
                        }
                        for a in upcoming
                    ]

                    missing_total += row["missing_assignments"]
                    upcoming_total += len(row["upcoming_assignments"])
                except Exception:
                    logger.debug("optional assignment data unavailable for child", exc_info=True)

            # Service hours
            if service_entry_model is not None:
                try:
                    core_student = _try_get_core_student(s, school_id=school_id)
                    if core_student:
                        approved = service_entry_model.objects.filter(
                            student=core_student, status="approved"
                        )
                        total_h = approved.aggregate(
                            total=Coalesce(Sum("hours"), Decimal("0"))
                        )["total"]
                        row["service_hours"] = {
                            "available": True,
                            "completed": float(_safe_decimal(total_h).quantize(Decimal("0.1"))),
                            "required": 30,
                        }
                except Exception:
                    logger.debug("optional service hours unavailable for child", exc_info=True)

            # Finance per student (invoice line student FK)
            if invoice_line_model is not None and invoice_model is not None:
                try:
                    lines = invoice_line_model.objects.filter(student=s).select_related("invoice")

                    inv_filter = Q()
                    if hasattr(invoice_model, "status"):
                        inv_filter = Q(invoice__status__in=["open", "unpaid", "pending"])
                    elif hasattr(invoice_model, "is_paid"):
                        inv_filter = Q(invoice__is_paid=False)

                    if inv_filter:
                        lines = lines.filter(inv_filter)

                    total_amount = lines.aggregate(
                        total=Coalesce(Sum("amount"), Decimal("0"))
                    )["total"]
                    row["financial"] = {
                        "available": True,
                        "balance_cents": int(
                            (_safe_decimal(total_amount) * Decimal("100")).quantize(Decimal("1"))
                        ),
                    }
                except Exception:
                    logger.debug("optional finance data unavailable for child", exc_info=True)

            # Alerts
            if row["current_average"] is not None and row["current_average"] < 75:
                row["alerts"].append({
                    "type": "academic",
                    "severity": "warning",
                    "message": f"{row['first_name']} has an average below 75%.",
                })
            if row["missing_assignments"] >= 3:
                row["alerts"].append({
                    "type": "work",
                    "severity": "warning",
                    "message": f"{row['first_name']} has 3+ missing assignments.",
                })

            child_rows.append(row)

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







