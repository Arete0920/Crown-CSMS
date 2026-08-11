from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from applications.models import (
    Application,
    Applicant,
    ApplicationEvent,
    EnrollmentContract,
    EnrollmentContractStatus,
)
from core.models import AcademicYear, UserAccount
from households.models import Household, Student

from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS


PARENT_EMAIL = SANDBOX_PERSONAS["parent"].email
SCHOOL_ID = uuid.UUID(SANDBOX_SCHOOLS["heritage-core"].id)
ENROLLMENT_DEMO_HOUSEHOLD = "Reed Family"
ENROLLMENT_DEMO_STUDENT_FIRST = "Jordan"
ENROLLMENT_DEMO_STUDENT_LAST = "Reed"
ENROLLMENT_DEMO_GRADE = "7"


class SandboxParentEnrollmentError(Exception):
    pass


@dataclass(frozen=True)
class SandboxEnrollmentState:
    application_id: str
    lifecycle_stage: str
    contract_status: str
    deposit_status: str
    applicant_to_student_status: str
    classroom_readiness_status: str
    parent_portal_activation_status: str
    child_id: str | None
    child_name: str
    demo_payment_processed: bool


def _sandbox_enabled() -> bool:
    return bool(getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", False))


def _require_parent(user) -> UserAccount:
    if not _sandbox_enabled():
        raise SandboxParentEnrollmentError("sandbox_open_session_required")
    if user is None or not getattr(user, "is_authenticated", False):
        raise SandboxParentEnrollmentError("authenticated_parent_required")
    if str(getattr(user, "email", "") or "").strip().lower() != PARENT_EMAIL:
        raise SandboxParentEnrollmentError("heritage_parent_required")
    if str(getattr(user, "school_id", "") or "") != str(SCHOOL_ID):
        raise SandboxParentEnrollmentError("heritage_school_required")
    return user


def _is_accepted(application: Application) -> bool:
    return ApplicationEvent.objects.filter(
        school_id=application.school_id,
        application=application,
        event_type="decision_made",
        payload__decision="accepted",
    ).exists()


def _is_enrolled(application: Application) -> bool:
    return ApplicationEvent.objects.filter(
        school_id=application.school_id,
        application=application,
        event_type="enrollment_confirmed",
    ).exists()


def _find_application(application_id: str | None = None) -> Application:
    qs = Application.objects.select_related("household").filter(
        school_id=SCHOOL_ID,
        household__name=ENROLLMENT_DEMO_HOUSEHOLD,
    )
    if application_id:
        qs = qs.filter(id=application_id)
    for application in qs.order_by("-created_at"):
        if _is_accepted(application) or _is_enrolled(application):
            return application
    raise SandboxParentEnrollmentError("accepted_application_not_found")


def _latest_enrollment_payload(application: Application) -> dict:
    event = (
        ApplicationEvent.objects.filter(
            school_id=application.school_id,
            application=application,
            event_type="enrollment_state_updated",
        )
        .order_by("-created_at")
        .first()
    )
    return dict(event.payload or {}) if event else {}


def _student_for_application(application: Application) -> Student | None:
    applicant = application.applicants.order_by("created_at").first()
    if applicant and applicant.student_id:
        return applicant.student
    if applicant:
        return Student.objects.filter(
            school_id=application.school_id,
            household=application.household,
            first_name=applicant.first_name,
            last_name=applicant.last_name,
        ).first()
    return None


def serialize_parent_enrollment_state(application: Application) -> SandboxEnrollmentState:
    payload = _latest_enrollment_payload(application)
    child = _student_for_application(application)
    enrolled = _is_enrolled(application)
    classroom_ready = ApplicationEvent.objects.filter(
        school_id=application.school_id,
        application=application,
        event_type="classroom_readiness_completed",
    ).exists()
    portal_active = ApplicationEvent.objects.filter(
        school_id=application.school_id,
        application=application,
        event_type="parent_portal_activated",
    ).exists()
    applicant = application.applicants.order_by("created_at").first()
    child_name = ""
    if applicant:
        child_name = f"{applicant.first_name} {applicant.last_name}".strip()
    return SandboxEnrollmentState(
        application_id=str(application.id),
        lifecycle_stage="enrolled" if enrolled else "accepted",
        contract_status=str(payload.get("contract_status") or "not_started"),
        deposit_status=str(payload.get("deposit_status") or "pending"),
        applicant_to_student_status="completed" if enrolled and child else ("ready" if _is_accepted(application) else "pending"),
        classroom_readiness_status="completed" if classroom_ready else ("in_progress" if enrolled else "pending"),
        parent_portal_activation_status="completed" if portal_active else ("in_progress" if enrolled else "pending"),
        child_id=str(child.id) if child else None,
        child_name=child_name,
        demo_payment_processed=False,
    )


def get_parent_enrollment_state(user, application_id: str | None = None) -> SandboxEnrollmentState:
    _require_parent(user)
    return serialize_parent_enrollment_state(_find_application(application_id))


def _ensure_contract(application: Application, parent_user: UserAccount) -> EnrollmentContract:
    contract = (
        EnrollmentContract.objects.filter(
            school_id=application.school_id,
            application=application,
        )
        .order_by("-version", "-created_at")
        .first()
    )
    if contract:
        return contract
    return EnrollmentContract.objects.create(
        school_id=application.school_id,
        application=application,
        version=1,
        status=EnrollmentContractStatus.ISSUED,
        line_items=[
            {"label": "Grade 7 Published Tuition", "category": "tuition", "amount_cents": 995000},
            {"label": "Enrollment deposit", "category": "deposit", "amount_cents": 25000},
        ],
        contract_totals={
            "gross_tuition_cents": 995000,
            "fees_cents": 0,
            "discounts_cents": 0,
            "aid_cents": 0,
            "scholarships_cents": 0,
            "esa_voucher_tax_credit_cents": 0,
            "donor_assistance_cents": 0,
            "deposit_cents": 25000,
            "amount_due_today_cents": 25000,
            "net_family_obligation_cents": 970000,
        },
        net_amount_cents=970000,
        currency="USD",
        payment_plan="Monthly",
        payment_schedule="Demo enrollment schedule",
        responsible_payer=parent_user.email,
        refund_terms="Demonstration agreement only. No external payment is processed.",
        note="Issued for the protected Heritage sandbox enrollment scenario.",
        issued_at=timezone.now(),
        created_by="sandbox-demo-orchestrator",
    )


def _event_once(application: Application, event_type: str, payload: dict) -> None:
    if ApplicationEvent.objects.filter(
        school_id=application.school_id,
        application=application,
        event_type=event_type,
    ).exists():
        return
    ApplicationEvent.objects.create(
        school_id=application.school_id,
        application=application,
        event_type=event_type,
        payload=payload,
    )


def _ensure_household_student(application: Application) -> Student:
    applicant = application.applicants.order_by("created_at").first()
    if applicant is None:
        raise SandboxParentEnrollmentError("applicant_not_found")
    if applicant.student_id:
        return applicant.student
    student, _ = Student.objects.update_or_create(
        school_id=application.school_id,
        household=application.household,
        first_name=applicant.first_name,
        last_name=applicant.last_name,
        defaults={
            "grade_level": applicant.grade_applying_for,
            "is_active": True,
        },
    )
    applicant.student = student
    applicant.save(update_fields=["student", "updated_at"])
    return student


@transaction.atomic
def complete_parent_enrollment_demo(user, application_id: str, accepted_terms: bool) -> SandboxEnrollmentState:
    parent_user = _require_parent(user)
    if not accepted_terms:
        raise SandboxParentEnrollmentError("enrollment_terms_required")

    application = _find_application(application_id)
    if not _is_accepted(application) and not _is_enrolled(application):
        raise SandboxParentEnrollmentError("application_not_accepted")

    if _is_enrolled(application):
        return serialize_parent_enrollment_state(application)

    contract = _ensure_contract(application, parent_user)
    now = timezone.now()

    contract.status = EnrollmentContractStatus.SIGNED
    contract.signed_at = contract.signed_at or now
    contract.responsible_payer = parent_user.email
    contract.note = "Parent accepted the protected Heritage sandbox enrollment agreement."
    contract.save(update_fields=["status", "signed_at", "responsible_payer", "note", "updated_at"])

    _event_once(
        application,
        "parent_enrollment_agreement_signed",
        {"updated_by": parent_user.email, "demo_only": True},
    )

    contract.status = EnrollmentContractStatus.COUNTERSIGNED
    contract.countersigned_at = contract.countersigned_at or now
    contract.note = "Sandbox school automation countersigned after parent acceptance; no external payment processed."
    contract.save(update_fields=["status", "countersigned_at", "note", "updated_at"])

    ApplicationEvent.objects.create(
        school_id=application.school_id,
        application=application,
        event_type="enrollment_state_updated",
        payload={
            "contract_status": "countersigned",
            "deposit_status": "paid",
            "note": "Protected sandbox deposit simulation; no payment provider called.",
            "transition_reason": "sandbox_parent_enrollment_demo",
            "owner_assignment": "Admissions / Finance automation",
            "updated_by": "sandbox-demo-orchestrator",
            "demo_payment_processed": False,
        },
    )
    _event_once(
        application,
        "sandbox_demo_deposit_simulated",
        {"amount_cents": 25000, "payment_processed": False, "updated_by": "sandbox-demo-orchestrator"},
    )

    student = _ensure_household_student(application)

    from admissions.models import AdmissionsApplication
    from applications.views_admissions import (
        _apply_lifecycle_chain_updates,
        _upsert_legacy_admissions_applications,
    )

    school_actor = UserAccount.objects.filter(
        school_id=application.school_id,
        username=SANDBOX_PERSONAS["school_admin"].email,
    ).first() or parent_user

    _events, lifecycle_error = _apply_lifecycle_chain_updates(
        app=application,
        actor_user=school_actor,
        note="Protected sandbox accepted-applicant enrollment after parent agreement; no external payment processed.",
        request_payload={"mark_enrollment_confirmed": True},
    )
    if lifecycle_error is not None:
        raise SandboxParentEnrollmentError("canonical_enrollment_gate_failed")

    _events, readiness_error = _apply_lifecycle_chain_updates(
        app=application,
        actor_user=school_actor,
        note="Protected sandbox post-enrollment readiness transition.",
        request_payload={
            "mark_classroom_ready": True,
            "mark_parent_portal_activated": True,
        },
    )
    if readiness_error is not None:
        raise SandboxParentEnrollmentError("canonical_post_enrollment_readiness_failed")

    bridge = _upsert_legacy_admissions_applications(
        app=application,
        actor_user=school_actor,
        target_status=AdmissionsApplication.STATUS_ENROLLED,
    )
    if bridge.get("state") != "enrolled" or int(bridge.get("count") or 0) < 1:
        raise SandboxParentEnrollmentError("enrollment_bridge_failed")

    state = serialize_parent_enrollment_state(application)
    if state.child_id != str(student.id):
        raise SandboxParentEnrollmentError("resulting_student_context_failed")
    return state


@transaction.atomic
def reset_parent_enrollment_scenario() -> None:
    """Delete only the deterministic accepted-applicant scenario before a flagship rebuild."""
    apps = list(
        Application.objects.filter(
            school_id=SCHOOL_ID,
            applicants__first_name=ENROLLMENT_DEMO_STUDENT_FIRST,
            applicants__last_name=ENROLLMENT_DEMO_STUDENT_LAST,
        )
        .select_related("household")
        .distinct()
    )
    household_ids = {app.household_id for app in apps}
    for application in apps:
        application.delete()
    if household_ids:
        Student.objects.filter(school_id=SCHOOL_ID, household_id__in=household_ids).delete()
        Household.objects.filter(
            school_id=SCHOOL_ID,
            id__in=household_ids,
            applications__isnull=True,
            students__isnull=True,
        ).delete()


@transaction.atomic
def seed_parent_enrollment_scenario() -> dict[str, str]:
    """Seed one deterministic accepted applicant for the buyer-facing Parent enrollment journey."""
    parent_user = UserAccount.objects.get(school_id=SCHOOL_ID, username=PARENT_EMAIL)
    reset_parent_enrollment_scenario()

    AcademicYear.objects.update_or_create(
        school_id=SCHOOL_ID,
        name="2026-2027",
        defaults={
            "start_date": date(2026, 8, 15),
            "end_date": date(2027, 6, 5),
            "is_current": True,
        },
    )

    household = Household.objects.create(
        school_id=SCHOOL_ID,
        name=ENROLLMENT_DEMO_HOUSEHOLD,
        address1="100 Demo Lane",
        city="Fairview",
        state="PA",
        postal_code="19000",
        is_active=True,
    )
    application = Application.objects.create(
        school_id=SCHOOL_ID,
        household=household,
        status="DECIDED",
        submitted_at=timezone.now(),
        decided_at=timezone.now(),
    )
    applicant = Applicant.objects.create(
        school_id=SCHOOL_ID,
        application=application,
        first_name=ENROLLMENT_DEMO_STUDENT_FIRST,
        last_name=ENROLLMENT_DEMO_STUDENT_LAST,
        grade_applying_for=ENROLLMENT_DEMO_GRADE,
        source="church_referral",
        flags={
            "guardians": [
                {
                    "guardianName": f"{parent_user.first_name} {parent_user.last_name}".strip(),
                    "email": parent_user.email,
                    "phone": "555-0100",
                    "relationship": "Mother",
                    "isPrimary": True,
                }
            ],
            "sandbox_demo": True,
        },
    )
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID,
        application=application,
        event_type="application_submitted",
        payload={"via": "sandbox_parent_enrollment_scenario", "applicant_id": str(applicant.id)},
    )
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID,
        application=application,
        event_type="decision_made",
        payload={"decision": "accepted", "updated_by": "sandbox-demo-orchestrator"},
    )
    contract = _ensure_contract(application, parent_user)
    ApplicationEvent.objects.create(
        school_id=SCHOOL_ID,
        application=application,
        event_type="enrollment_state_updated",
        payload={
            "contract_status": "sent",
            "deposit_status": "invoiced",
            "note": "Enrollment agreement ready for parent action.",
            "transition_reason": "sandbox_seed",
            "updated_by": "sandbox-demo-orchestrator",
            "demo_payment_processed": False,
        },
    )
    return {
        "parent_enrollment_application_id": str(application.id),
        "parent_enrollment_contract_id": str(contract.id),
    }
