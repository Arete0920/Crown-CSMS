"""
Admissions stage transition service.

Provides guarded move_stage() that enforces allowed transitions.
Direct calls to AdmissionsApplication.set_status() bypass this guard;
use move_stage() for all external/API-triggered status changes.

Note: billing hooks (create_obligation) are intentionally omitted here.
When ledger integration is needed, wire via ledger.services after move_stage().
"""

from .models import AdmissionsApplication


# -----------------------------------------------------------------------
# Allowed transition graph (status → set of valid next statuses)
# -----------------------------------------------------------------------

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
    # Terminal statuses — no outbound transitions
    # DENIED, ENROLLED, WITHDRAWN: intentionally absent
}


class InvalidStageTransition(Exception):
    """Raised when a status transition is not in ALLOWED_TRANSITIONS."""


def move_stage(
    record: AdmissionsApplication,
    new_status: str,
    actor_user=None,
    details: dict | None = None,
) -> AdmissionsApplication:
    """
    Validate and execute a status transition for an AdmissionsApplication.

    Raises InvalidStageTransition if the transition is not permitted.
    Calls record.set_status() which handles save + audit event creation.
    """
    allowed = ALLOWED_TRANSITIONS.get(record.status, set())
    if new_status not in allowed:
        raise InvalidStageTransition(
            f"Invalid transition: {record.status!r} → {new_status!r}. "
            f"Allowed: {sorted(allowed) or 'none (terminal status)'}"
        )

    record.set_status(new_status, actor_user=actor_user, details=details or {})
    return record
