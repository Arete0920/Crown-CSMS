"""
Aftercare integration hooks.

These hooks are the canonical seam between aftercare services and the finance/
discipline subsystems. In this workspace they are implemented as deterministic
no-op stubs so the service layer can be exercised without external coupling.
"""


def create_aftercare_finance_obligation(
    school_id: int,
    student_id: int,
    amount_cents: int,
    description: str,
) -> int:
    """Return a stable placeholder obligation ID for aftercare tests."""
    return 0


def create_aftercare_discipline_incident(
    school_id: int,
    student_id: int,
    description: str,
    severity: str,
):
    """Return a stable placeholder incident ID for aftercare tests."""
    return 0
