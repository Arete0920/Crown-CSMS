"""Admissions lifecycle services.

External/API-triggered stage changes must use :func:`move_stage` so the
transition graph and audit trail remain authoritative. Enrollment conversion
uses :func:`finalize_enrollment`, which applies the guarded ACCEPTED -> ENROLLED
transition and activates the linked SIS student in one transaction.

Financial obligations and enrollment-contract readiness belong to the newer
``applications`` domain. They are intentionally not inferred here until a
verified relational authority links those records to ``AdmissionsApplication``.
"""

from django.db import transaction

from .models import AdmissionsApplication


ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    AdmissionsApplication.STATUS_DRAFT: {
        AdmissionsApplication.STATUS_SUBMITTED,
        AdmissionsApplication.STATUS_WITHDRAWN,
    },
    AdmissionsApplication.STATUS_SUBMITTED: {
        AdmissionsApplication.STATUS_UNDER_REVIEW,
        AdmissionsApplication.STATUS_NEEDS_INFO,
        AdmissionsApplication.STATUS_WITHDRAWN,
    },
    AdmissionsApplication.STATUS_UNDER_REVIEW: {
        AdmissionsApplication.STATUS_ACCEPTED,
        AdmissionsApplication.STATUS_WAITLISTED,
        AdmissionsApplication.STATUS_DENIED,
        AdmissionsApplication.STATUS_NEEDS_INFO,
        AdmissionsApplication.STATUS_WITHDRAWN,
    },
    AdmissionsApplication.STATUS_NEEDS_INFO: {
        AdmissionsApplication.STATUS_SUBMITTED,
        AdmissionsApplication.STATUS_WITHDRAWN,
    },
    AdmissionsApplication.STATUS_ACCEPTED: {
        AdmissionsApplication.STATUS_ENROLLED,
        AdmissionsApplication.STATUS_WITHDRAWN,
    },
    AdmissionsApplication.STATUS_WAITLISTED: {
        AdmissionsApplication.STATUS_ACCEPTED,
        AdmissionsApplication.STATUS_DENIED,
        AdmissionsApplication.STATUS_WITHDRAWN,
    },
    # DENIED, ENROLLED, and WITHDRAWN are terminal.
}


class InvalidStageTransition(Exception):
    """Raised when a requested application transition is not permitted."""


def move_stage(
    record: AdmissionsApplication,
    new_status: str,
    actor_user=None,
    details: dict | None = None,
) -> AdmissionsApplication:
    """Validate and execute one audited admissions application transition."""
    allowed = ALLOWED_TRANSITIONS.get(record.status, set())
    if new_status not in allowed:
        raise InvalidStageTransition(
            f"Invalid transition: {record.status!r} -> {new_status!r}. "
            f"Allowed: {sorted(allowed) or 'none (terminal status)'}"
        )

    record.set_status(new_status, actor_user=actor_user, details=details or {})
    return record


def _finalize_enrollment_locked(
    record: AdmissionsApplication,
    *,
    actor_user=None,
    details: dict | None = None,
) -> tuple[AdmissionsApplication, bool]:
    record = AdmissionsApplication.objects.select_for_update().get(pk=record.pk)

    if record.status == AdmissionsApplication.STATUS_ENROLLED:
        return record, False

    move_stage(
        record,
        AdmissionsApplication.STATUS_ENROLLED,
        actor_user=actor_user,
        details=details or {"source": "enrollment_conversion"},
    )

    if record.sis_student_id:
        sis_student = record.sis_student
        if not sis_student.active:
            sis_student.active = True
            sis_student.save(update_fields=["active"])

    return record, True


def finalize_enrollment(
    record: AdmissionsApplication,
    *,
    actor_user=None,
    details: dict | None = None,
) -> tuple[AdmissionsApplication, bool]:
    """Finalize one legacy admissions application into the enrolled state.

    Returns ``(record, converted)``. The authoritative row is reloaded under a
    database lock before the status check so repeated or concurrent calls are
    idempotent. If the caller already owns a transaction, that transaction is
    reused without creating a per-record savepoint. Standalone callers receive
    an atomic transaction owned by this service.
    """
    using = record._state.db or "default"
    connection = transaction.get_connection(using=using)
    if connection.in_atomic_block:
        return _finalize_enrollment_locked(
            record,
            actor_user=actor_user,
            details=details,
        )

    with transaction.atomic(using=using):
        return _finalize_enrollment_locked(
            record,
            actor_user=actor_user,
            details=details,
        )
