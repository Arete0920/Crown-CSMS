"""Canonical integration seams for extended care.

Every integration either performs a verified write or raises
AftercareIntegrationError. Placeholder success values are prohibited.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone


class AftercareIntegrationError(ValueError):
    """Raised when a canonical downstream write cannot be proven safe."""


@transaction.atomic
def create_aftercare_finance_obligation(
    school_id,
    student_id,
    amount_cents: int,
    description: str,
) -> int:
    """Create and ledger-post a real FinanceObligation for a canonical student."""
    from core.models import School
    from finance.models import FinanceObligation, ObligationType
    from finance.services import ledger_post_obligation
    from households.models import Guardian, Student

    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None:
        raise AftercareIntegrationError("Canonical school not found.")

    student = (
        Student.objects.select_related("household")
        .filter(pk=student_id, school_id=school.id, is_active=True)
        .first()
    )
    if student is None:
        raise AftercareIntegrationError("Canonical student is not active in this school.")

    guardians = list(
        Guardian.objects.select_related("account")
        .filter(
            school_id=school.id,
            household=student.household,
            account__isnull=False,
            is_primary=True,
        )[:2]
    )
    if not guardians:
        guardians = list(
            Guardian.objects.select_related("account")
            .filter(
                school_id=school.id,
                household=student.household,
                account__isnull=False,
            )[:2]
        )
    if len(guardians) != 1:
        raise AftercareIntegrationError(
            "Exactly one authenticated payer guardian is required for extended-care billing."
        )

    payer = guardians[0].account
    if payer is None or payer.school_id != school.id:
        raise AftercareIntegrationError("Payer account is not scoped to the student's school.")

    obligation = FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.FEE,
        description=description,
        due_date=timezone.localdate(),
        amount_cents=int(amount_cents),
        reference=f"extended-care:{student.id}",
    )
    post_result = ledger_post_obligation(obligation)
    if not post_result.ok:
        raise AftercareIntegrationError(
            f"Extended-care ledger posting failed: {post_result.reference}"
        )
    return obligation.pk


def create_aftercare_discipline_incident(
    school_id,
    student_id,
    description: str,
    severity: str,
):
    """Fail closed until a verified households.Student -> core.Student bridge exists."""
    from core.models import School
    from households.models import Student

    if not School.objects.filter(pk=school_id, is_active=True).exists():
        raise AftercareIntegrationError("Canonical school not found.")
    if not Student.objects.filter(pk=student_id, school_id=school_id, is_active=True).exists():
        raise AftercareIntegrationError("Canonical student is not active in this school.")

    raise AftercareIntegrationError(
        "Discipline write blocked: no verified canonical mapping from households.Student "
        "to core.Student exists. Synthetic matching is prohibited."
    )
