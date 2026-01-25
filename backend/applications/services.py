from __future__ import annotations

from dataclasses import dataclass
from django.db import transaction
from django.utils import timezone

from households.models import Student
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


def decide_application(
    *,
    application,
    decision: str,
    enrollment_fee_amount=None,
):
    """
    decision: "ACCEPT" or "DENY"
    enrollment_fee_amount: Decimal or None
    """
    from .models import ApplicationStatus, ApplicationEvent

    if decision not in ("ACCEPT", "DENY"):
        raise ValueError("decision must be ACCEPT or DENY")

    if application.status != ApplicationStatus.SUBMITTED:
        raise ValueError("Only SUBMITTED applications can be decided")

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

        # ACCEPT FLOW
        application.status = ApplicationStatus.DECIDED
        application.decided_at = timezone.now()
        application.save(update_fields=["status", "decided_at", "updated_at"])

        ApplicationEvent.objects.create(
            school_id=application.school_id,
            application=application,
            event_type="APPLICATION_ACCEPTED",
            payload={},
        )

        created_students = []

        for applicant in application.applicants.all():
            student = Student.objects.create(
                school_id=application.school_id,
                household=application.household,
                first_name=applicant.first_name,
                last_name=applicant.last_name,
                grade_level=applicant.grade_applying_for or "",
                is_active=True,
            )
            created_students.append(student)

            ApplicationEvent.objects.create(
                school_id=application.school_id,
                application=application,
                event_type="STUDENT_CREATED",
                payload={"student_id": str(student.id)},
            )

        # Ensure ledger account
        acct, _ = LedgerAccount.objects.get_or_create(
            school_id=application.school_id,
            household=application.household,
        )

        # Optional enrollment fee
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
