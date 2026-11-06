from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import date

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from applications.services import _provision_student_identity, has_verified_student_enrollments
from applications.models import (
    Application,
    Applicant,
    ApplicationEvent,
    EnrollmentContract,
    EnrollmentContractStatus,
)
from core.models import (
    AcademicYear,
    Enrollment as CoreEnrollment,
    GradeLevel,
    HouseholdFamilyLink,
    School,
    Student as CoreStudent,
    StudentIdentityLink,
    StudentTuition,
    LedgerEntry,
    UserAccount,
)
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


def _scenario_application_ids():
    """Identify this seeded scenario by both applicant and explicit seed evidence."""
    return Application.objects.filter(
        school_id=SCHOOL_ID,
        household__name=ENROLLMENT_DEMO_HOUSEHOLD,
        applicants__first_name=ENROLLMENT_DEMO_STUDENT_FIRST,
        applicants__last_name=ENROLLMENT_DEMO_STUDENT_LAST,
        applicants__flags__sandbox_demo=True,
        events__event_type="application_submitted",
        events__payload__via="sandbox_parent_enrollment_scenario",
    ).values_list("id", flat=True)


def _find_application(
    application_id: str | None = None, *, for_update: bool = False
) -> Application:
    # An IN subquery avoids DISTINCT on the locked PostgreSQL outer query.
    qs = Application.objects.select_related("household").filter(
        school_id=SCHOOL_ID, id__in=_scenario_application_ids()
    )
    if application_id:
        qs = qs.filter(id=application_id)
    if for_update:
        qs = qs.select_for_update(of=("self",))
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
    return None


def serialize_parent_enrollment_state(application: Application) -> SandboxEnrollmentState:
    payload = _latest_enrollment_payload(application)
    child = _student_for_application(application)
    enrolled = _is_enrolled(application)
    authoritative_ready = enrolled and has_verified_student_enrollments(application)
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
        applicant_to_student_status="completed" if authoritative_ready and child else ("in_progress" if enrolled else ("ready" if _is_accepted(application) else "pending")),
        classroom_readiness_status="completed" if authoritative_ready and classroom_ready else ("in_progress" if enrolled else "pending"),
        parent_portal_activation_status="completed" if authoritative_ready and portal_active else ("in_progress" if enrolled else "pending"),
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


def _provision_verified_parent_applicant(application: Application):
    """Use the canonical admissions writer; never identify a child by name."""
    from applications.views_admissions import _resolve_or_create_legacy_family

    applicants = list(application.applicants.order_by("created_at", "id"))
    if len(applicants) != 1:
        raise SandboxParentEnrollmentError("single_verified_applicant_required")
    applicant = applicants[0]
    if applicant.dob is None:
        raise SandboxParentEnrollmentError("verified_date_of_birth_required")
    school = School.objects.filter(id=application.school_id).first()
    if school is None:
        raise SandboxParentEnrollmentError("school_not_found")
    family = _resolve_or_create_legacy_family(
        school=school, household=application.household
    )
    if family is None:
        raise SandboxParentEnrollmentError("verified_family_required")
    student_number = f"APP-{str(application.id).replace('-', '')[:6]}-01"
    try:
        compatibility_student, core_student, _created = _provision_student_identity(
            application=application,
            applicant=applicant,
            family=family,
            student_numbers={str(applicant.id): student_number},
        )
    except ValueError as exc:
        raise SandboxParentEnrollmentError("verified_student_identity_required") from exc
    if (
        core_student.school_id != application.school_id
        or core_student.family_id != family.id
        or core_student.dob != applicant.dob
    ):
        raise SandboxParentEnrollmentError("canonical_identity_mismatch")
    return compatibility_student, core_student, applicant


def _ensure_core_enrollment(
    application: Application, core_student: CoreStudent, applicant: Applicant, legacy_bridge: dict
):
    """Persist the authoritative school-year enrollment, not only a legacy flag."""
    from admissions.models import AdmissionsApplication

    synced_ids = legacy_bridge.get("application_ids") or []
    if len(synced_ids) != 1:
        raise SandboxParentEnrollmentError("legacy_application_count_mismatch")
    legacy = AdmissionsApplication.objects.filter(
        pk=synced_ids[0], school_id=application.school_id
    ).select_related("academic_year").first()
    if legacy is None or legacy.student_id != core_student.id:
        raise SandboxParentEnrollmentError("legacy_student_identity_mismatch")
    year = legacy.academic_year
    grade = GradeLevel.objects.filter(
        school_id=application.school_id, code=applicant.grade_applying_for
    ).first()
    if (
        year is None or year.school_id != application.school_id
        or grade is None or core_student.school_id != application.school_id
    ):
        raise SandboxParentEnrollmentError("canonical_enrollment_configuration_missing")
    if core_student.current_grade_level_id not in (None, grade.id):
        raise SandboxParentEnrollmentError("canonical_grade_conflict")
    if core_student.current_grade_level_id is None:
        core_student.current_grade_level = grade
        core_student.save(update_fields=["current_grade_level", "updated_at"])
    start_date = max(timezone.localdate(), year.start_date)
    if start_date > year.end_date:
        raise SandboxParentEnrollmentError("academic_year_expired")
    enrollment, _created = CoreEnrollment.objects.get_or_create(
        school_id=application.school_id,
        student=core_student,
        academic_year=year,
        defaults={
            "grade_level": grade,
            "start_date": start_date,
            "status": "ENROLLED",
        },
    )
    if enrollment.grade_level_id != grade.id or enrollment.status != "ENROLLED":
        raise SandboxParentEnrollmentError("canonical_enrollment_conflict")
    return enrollment

@transaction.atomic
def complete_parent_enrollment_demo(user, application_id: str, accepted_terms: bool) -> SandboxEnrollmentState:
    parent_user = _require_parent(user)
    if not accepted_terms:
        raise SandboxParentEnrollmentError("enrollment_terms_required")

    application = _find_application(application_id, for_update=True)
    if not _is_accepted(application) and not _is_enrolled(application):
        raise SandboxParentEnrollmentError("application_not_accepted")

    if _is_enrolled(application):
        state = serialize_parent_enrollment_state(application)
        if state.applicant_to_student_status != "completed":
            raise SandboxParentEnrollmentError("canonical_enrollment_verification_failed")
        return state

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

    student, core_student, applicant = _provision_verified_parent_applicant(application)

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
    if bridge.get("state") != "enrolled" or int(bridge.get("count") or 0) != 1:
        raise SandboxParentEnrollmentError("enrollment_bridge_failed")
    _ensure_core_enrollment(application, core_student, applicant, bridge)

    state = serialize_parent_enrollment_state(application)
    if state.applicant_to_student_status != "completed":
        raise SandboxParentEnrollmentError("canonical_enrollment_verification_failed")
    if state.child_id != str(student.id):
        raise SandboxParentEnrollmentError("resulting_student_context_failed")
    return state


def _require_pristine_parent_scenario_events(application: Application) -> None:
    """Never erase an unexpected, duplicated or edited application event."""
    applicants = list(application.applicants.order_by("created_at", "id")[:2])
    if len(applicants) != 1:
        raise SandboxParentEnrollmentError("reset_application_history_not_synthetic")
    applicant = applicants[0]
    seed = [
        ("application_submitted", {
            "via": "sandbox_parent_enrollment_scenario", "applicant_id": str(applicant.id),
        }),
        ("decision_made", {
            "decision": "accepted", "updated_by": "sandbox-demo-orchestrator",
        }),
        ("enrollment_state_updated", {
            "contract_status": "sent", "deposit_status": "invoiced",
            "note": "Enrollment agreement ready for parent action.",
            "transition_reason": "sandbox_seed",
            "updated_by": "sandbox-demo-orchestrator",
            "demo_payment_processed": False,
        }),
    ]
    observed = list(ApplicationEvent.objects.filter(
        school_id=SCHOOL_ID, application=application,
    ).values_list("event_type", "payload"))

    def fingerprint(events):
        return sorted((kind, json.dumps(payload, sort_keys=True)) for kind, payload in events)

    if fingerprint(observed) == fingerprint(seed):
        return
    for actor in {PARENT_EMAIL, SANDBOX_PERSONAS["school_admin"].email}:
        completed = seed + [
            ("parent_enrollment_agreement_signed", {
                "updated_by": PARENT_EMAIL, "demo_only": True,
            }),
            ("enrollment_state_updated", {
                "contract_status": "countersigned", "deposit_status": "paid",
                "note": "Protected sandbox deposit simulation; no payment provider called.",
                "transition_reason": "sandbox_parent_enrollment_demo",
                "owner_assignment": "Admissions / Finance automation",
                "updated_by": "sandbox-demo-orchestrator",
                "demo_payment_processed": False,
            }),
            ("sandbox_demo_deposit_simulated", {
                "amount_cents": 25000, "payment_processed": False,
                "updated_by": "sandbox-demo-orchestrator",
            }),
            ("enrollment_confirmed", {
                "note": "Protected sandbox accepted-applicant enrollment after parent agreement; no external payment processed.",
                "updated_by": actor,
            }),
            ("classroom_readiness_completed", {
                "note": "Protected sandbox post-enrollment readiness transition.",
                "updated_by": actor,
            }),
            ("parent_portal_activated", {
                "note": "Protected sandbox post-enrollment readiness transition.",
                "updated_by": actor,
            }),
        ]
        if fingerprint(observed) == fingerprint(completed):
            return
    raise SandboxParentEnrollmentError("reset_application_history_not_synthetic")


@transaction.atomic
def reset_parent_enrollment_scenario() -> None:
    """Reset only exact fictional records; reject unrelated audit history."""
    from admissions.models import AdmissionsApplication, AdmissionsAuditEvent

    apps = list(
        Application.objects.select_for_update(of=("self",))
        .filter(school_id=SCHOOL_ID, id__in=_scenario_application_ids())
        .select_related("household")
        .order_by("id")
    )
    app_ids = {app.id for app in apps}
    household_ids = {app.household_id for app in apps}
    owned_compatibility_ids = set()

    # Validate all dependencies before deleting anything; atomicity also
    # guarantees rollback if a later database constraint rejects a delete.
    deletions = []
    for application in apps:
        _require_pristine_parent_scenario_events(application)
        for applicant in application.applicants.all():
            if not applicant.student_id:
                continue
            link = (
                StudentIdentityLink.objects.select_related(
                    "core_student", "compatibility_student"
                )
                .filter(
                    school_id=SCHOOL_ID,
                    compatibility_student_id=applicant.student_id,
                    source=StudentIdentityLink.SOURCE_ADMISSIONS,
                    evidence_reference=(
                        f"application:{application.id}:applicant:{applicant.id}"
                    ),
                )
                .first()
            )
            if (
                link is None
                or link.compatibility_student.household_id != application.household_id
                or link.compatibility_student.account_id is not None
                or link.core_student.school_id != SCHOOL_ID
            ):
                raise SandboxParentEnrollmentError("reset_identity_not_exclusively_synthetic")
            if Applicant.objects.filter(student_id=applicant.student_id).exclude(
                application_id__in=app_ids
            ).exists():
                raise SandboxParentEnrollmentError("reset_student_referenced_elsewhere")
            owned_legacy = AdmissionsApplication.objects.filter(
                school_id=SCHOOL_ID,
                student=link.core_student,
                notes_internal__contains=f"canonical_application_id={application.id}",
            )
            owned_legacy_ids = list(owned_legacy.values_list("id", flat=True))
            if AdmissionsAuditEvent.objects.filter(
                school_id=SCHOOL_ID,
                entity_type=AdmissionsAuditEvent.ENTITY_APPLICATION,
                entity_id__in=[str(legacy_id) for legacy_id in owned_legacy_ids],
            ).exists():
                raise SandboxParentEnrollmentError("reset_historical_admissions_audit_exists")
            owned_year_ids = list(owned_legacy.values_list("academic_year_id", flat=True))
            if AdmissionsApplication.objects.filter(
                student=link.core_student
            ).exclude(id__in=owned_legacy_ids).exists():
                raise SandboxParentEnrollmentError("reset_legacy_student_shared")
            if CoreEnrollment.objects.filter(
                student=link.core_student
            ).exclude(academic_year_id__in=owned_year_ids).exists():
                raise SandboxParentEnrollmentError("reset_student_has_external_enrollment")
            if (
                StudentTuition.objects.filter(student=link.core_student).exists()
                or LedgerEntry.objects.filter(student=link.core_student).exists()
            ):
                raise SandboxParentEnrollmentError("reset_student_has_financial_history")
            owned_compatibility_ids.add(applicant.student_id)
            deletions.append((link, owned_legacy_ids, owned_year_ids))

    for link, legacy_ids, year_ids in deletions:
        core_student = link.core_student
        AdmissionsApplication.objects.filter(id__in=legacy_ids).delete()
        CoreEnrollment.objects.filter(
            student=core_student, academic_year_id__in=year_ids
        ).delete()
        link.delete()
        core_student.delete()
    for application in apps:
        application.delete()

    # Never delete other compatibility students merely because they share a
    # household, student name or school with the fictional scenario.
    if owned_compatibility_ids:
        Student.objects.filter(
            school_id=SCHOOL_ID, id__in=owned_compatibility_ids
        ).delete()

    for link in HouseholdFamilyLink.objects.filter(
        school_id=SCHOOL_ID, household_id__in=household_ids,
        source=HouseholdFamilyLink.SOURCE_ADMISSIONS,
    ):
        if (
            CoreStudent.objects.filter(family_id=link.family_id).exists()
            or Application.objects.filter(household_id=link.household_id).exists()
            or Student.objects.filter(household_id=link.household_id).exists()
            or Household.objects.filter(
                id=link.household_id, guardians__isnull=False
            ).exists()
        ):
            continue
        link.delete()
    Household.objects.filter(
        school_id=SCHOOL_ID,
        id__in=household_ids,
        applications__isnull=True,
        students__isnull=True,
        guardians__isnull=True,
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
    GradeLevel.objects.get_or_create(
        school_id=SCHOOL_ID,
        code=ENROLLMENT_DEMO_GRADE,
        defaults={"label": "Grade 7", "sort_order": 7},
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
        dob=date(2013, 2, 15),  # Explicit, fictional fixture DOB, never inferred.
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
