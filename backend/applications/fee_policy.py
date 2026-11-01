"""School/term-scoped admissions application-fee quotes.

These are process fees, not tuition, enrollment deposits or Jireh application
fees. Only the active, committed Fee Schedule can authorize an admissions fee.
Never substitute a deployment-wide default for a missing tenant quote.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from fee_schedule_wizard.models import FeeLine, FeeSchedule


FIRST_CHILD_FEE_CODE = "admissions_first_child"
ADDITIONAL_CHILD_FEE_CODE = "admissions_additional_child"
JIREH_FAMILY_FEE_CODE = "jireh_family_application"  # Separate Jireh charge; not billed by admissions.


@dataclass(frozen=True)
class AdmissionsFeePolicy:
    school_id: str
    term: str
    schedule_id: str
    first_child_cents: int
    additional_child_cents: int

    def amount_for_child(self, child_index: int) -> Decimal:
        if child_index < 1:
            raise ValueError("child_index must be positive")
        cents = self.first_child_cents if child_index == 1 else self.additional_child_cents
        return (Decimal(cents) / 100).quantize(Decimal("0.01"))

    @property
    def required(self) -> bool:
        return self.first_child_cents > 0 or self.additional_child_cents > 0


def get_admissions_fee_policy(*, school, term: str) -> AdmissionsFeePolicy | None:
    """Return a complete, verified school/term policy or None (unconfigured).

    The Fee Schedule Wizard ensures that active published schedules are
    school-scoped. Defensive checks reject ambiguous/malformed legacy rows.
    """
    term = str(term or "").strip()
    if not school or not term:
        return None

    codes = (FIRST_CHILD_FEE_CODE, ADDITIONAL_CHILD_FEE_CODE)
    # A school may publish tuition, activity and admissions schedules for the
    # same term. Select only schedules containing BOTH admissions fee lines.
    # Two complete candidates are ambiguous and must fail closed.
    schedules = list(
        FeeSchedule.objects.filter(
            school_id=school.pk, term=term, is_active=True,
            lines__code=FIRST_CHILD_FEE_CODE,
        ).filter(
            lines__code=ADDITIONAL_CHILD_FEE_CODE,
        ).distinct().only("id")[:2]
    )
    if len(schedules) != 1:
        return None

    schedule = schedules[0]
    lines = list(
        FeeLine.objects.filter(fee_schedule=schedule, code__in=codes)
        .values("code", "amount_cents", "kind", "frequency", "is_required")
    )
    if len(lines) != 2:
        return None
    by_code = {line["code"]: line for line in lines}
    if set(by_code) != set(codes):
        return None

    for line in by_code.values():
        if line["kind"] != FeeLine.KIND_FEE or line["frequency"] != FeeLine.FREQ_ONE_TIME:
            return None
        if line["is_required"] is not True:
            return None
        if type(line["amount_cents"]) is not int or line["amount_cents"] < 0:
            return None

    return AdmissionsFeePolicy(
        school_id=str(school.pk),
        term=term,
        schedule_id=str(schedule.pk),
        first_child_cents=by_code[FIRST_CHILD_FEE_CODE]["amount_cents"],
        additional_child_cents=by_code[ADDITIONAL_CHILD_FEE_CODE]["amount_cents"],
    )
