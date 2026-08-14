from __future__ import annotations

from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone

from core.models import HouseholdFamilyLink, Student as CoreStudent, StudentIdentityLink
from households.models import Student as CompatibilityStudent
from ledger.models import LedgerAccount, Charge

from .models import Application, ApplicationEvent, ApplicationStatus


@dataclass(frozen=True)
class TransitionResult:
    application: Application


def submit_application(app: Application) -> TransitionResult:
    if app.status != ApplicationStatus.DRAFT:
        raise ValueError("Only DRAFT applications can be submitted.")

    app.status = ApplicationStatus.SUBMITTED
    app.submitted_at = timezone.now()
    app.save(update_fields=["status", "submitted_at", "updated_at"])

    ApplicationEvent.objects.create(
        school_id=app.school_id,
        application=app,
        event_type="APPLICATION_SUBMITTED",
        payload={},
    )

    return TransitionResult(application=app)


def _student_number_for(applicant, student_numbers: dict[str, str]) -> str:
    value = str(student_numbers.get(str(applicant.id), "") or "").strip()
    if not value:
        raise ValueError(
            f"An explicit student number is required for applicant {applicant.id}."
        )
    return value


def _family_for_application(application):
    links = list(
        HouseholdFamilyLink.objects.select_related("family").filter(
            school_id=application.school_id,
            household_id=application.household_id,
        )
    )
    if len(links) != 1:
        raise ValueError(
            "Application acceptance requires exactly one verified household-to-family link."
        )
    return links[0].family


def _provision_student_identity(*, application, applicant, family, student_numbers):
    compatibility_student = applicant.student
    if compatibility_student is not None:
        if compatibility_student.school_id != application.school_id:
            raise ValueError("Applicant student belongs to a different school.")
        if compatibility_student.household_id != application.household_id:
            raise ValueError("Applicant student belongs to a different household.")

        existing_link = StudentIdentityLink.objects.select_related("core_student").filter(
            compatibility_student=compatibility_student,
        ).first()
        if existing_link is not None:
            if (
                existing_link.school_id != application.school_id
                or existing_link.verification_status != StudentIdentityLink.STATUS_VERIFIED
            ):
                raise ValueError("Applicant student identity link is not verified for this school.")
            return compatibility_student, existing_link.core_student, False

    if applicant.dob is None:
        raise ValueError(
            f"A verified date of birth is required for applicant {applicant.id}."
        )

    student_number = _student_number_for(applicant, student_numbers)
    if CoreStudent.objects.filter(
        school_id=application.school_id,
        student_number=student_number,
    ).exists():
        raise ValueError(
            f"Student number {student_number} already exists; identity must be reconciled explicitly."
        )

    core_student = CoreStudent.objects.create(
        school_id=application.school_id,
        family=family,
        student_number=student_number,
        first_name=applicant.first_name,
        last_name=applicant.last_name,
        dob=applicant.dob,
        status="ACTIVE",
    )

    if compatibility_student is None:
        compatibility_student = CompatibilityStudent.objects.create(
            school_id=application.school_id,
            household=application.household,
            first_name=applicant.first_name,
            last_name=applicant.last_name,
            grade_level=applicant.grade_applying_for or "",
            is_active=True,
        )
        applicant.student = compatibility_student
        applicant.save(update_fields=["student", "updated_at"])

    identity_link = StudentIdentityLink.objects.create(
        school_id=application.school_id,
        core_student=core_student,
        compatibility_student=compatibility_student,
        source=StudentIdentityLink.SOURCE_ADMISSIONS,
        verification_status=StudentIdentityLink.STATUS_VERIFIED,
        evidence_reference=f"application:{application.id}:applicant:{applicant.id}",
    )
    return compatibility_student, core_student, True


def decide_application(
    *,
    application,
    decision: str,
    enrollment_fee_amount=None,
    student_numbers: dict[str, str] | None = None,
):
    """
    decision: "ACCEPT" or "DENY"
    enrollment_fee_amount: Decimal or None
    student_numbers: mapping of applicant UUID string -> explicit canonical student number
    """
    from .models import ApplicationStatus, ApplicationEvent

    if decision not in ("ACCEPT", "DENY"):
        raise ValueError("decision must be ACCEPT or DENY")

    if application.status != ApplicationStatus.SUBMITTED:
        raise ValueError("Only SUBMITTED applications can be decided")

    normalized_student_numbers = student_numbers or {}
    if not isinstance(normalized_student_numbers, dict):
        raise ValueError("student_numbers must be an object keyed by applicant id")

    with transaction.atomic():
        if decision == "DENY":
            application.status = ApplicationStatus.DECIDED
            application.decided_at = timezone.now()
            application.save(update_fields=["status", "decided_at", "updated_at"])

            ApplicationEvent.objects.create(
                school_id=application.school_id,
                application=application,
                event_type="APPLICATION_DENIED",
                payload={},
            )
            return []

        applicants = list(application.applicants.select_for_update().all())
        if not applicants:
            raise ValueError("Application acceptance requires at least one applicant.")

        family = _family_for_application(application)
        created_students = []

        for applicant in applicants:
            compatibility_student, core_student, created = _provision_student_identity(
                application=application,
                applicant=applicant,
                family=family,
                student_numbers=normalized_student_numbers,
            )
            created_students.append(compatibility_student)

            ApplicationEvent.objects.create(
                school_id=application.school_id,
                application=application,
                event_type="STUDENT_IDENTITY_CREATED" if created else "STUDENT_IDENTITY_REUSED",
                payload={
                    "student_id": str(compatibility_student.id),
                    "core_student_id": str(core_student.id),
                    "applicant_id": str(applicant.id),
                },
            )

        application.status = ApplicationStatus.DECIDED
        application.decided_at = timezone.now()
        application.save(update_fields=["status", "decided_at", "updated_at"])

        ApplicationEvent.objects.create(
            school_id=application.school_id,
            application=application,
            event_type="APPLICATION_ACCEPTED",
            payload={},
        )

        acct, _ = LedgerAccount.objects.get_or_create(
            school_id=application.school_id,
            household=application.household,
        )

        if enrollment_fee_amount is not None:
            Charge.objects.create(
                school_id=application.school_id,
                account=acct,
                description="Enrollment Fee",
                amount=enrollment_fee_amount,
            )

            ApplicationEvent.objects.create(
                school_id=application.school_id,
                application=application,
                event_type="ENROLLMENT_FEE_CHARGED",
                payload={"amount": str(enrollment_fee_amount)},
            )

        return created_students
