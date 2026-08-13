from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

from core.models import TuitionPlan

from .models import FinancialAidApplication


DEFAULT_TUITION_ESTIMATE = Decimal("12000.00")
NEUTRAL_INCOME_FACTOR = 0.5
RETURNING_FAMILY_FACTOR = 0.3


def _to_decimal(value: object, *, default: Decimal = Decimal("0")) -> Decimal:
    if value in (None, ""):
        return default
    try:
        return Decimal(str(value))
    except (ArithmeticError, TypeError, ValueError):
        return default


def _to_int(value: object, *, default: int = 0) -> int:
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp_unit(value: Decimal | float | int) -> float:
    numeric = float(value)
    return max(0.0, min(1.0, numeric))


def _resolve_tuition_estimate(application: FinancialAidApplication) -> Decimal:
    direct_estimate = _to_decimal(
        getattr(application, "school_tuition_estimate", None),
        default=Decimal("0"),
    )
    if direct_estimate > 0:
        return direct_estimate

    school_id = getattr(application, "school_id", None)
    academic_year = getattr(application, "academic_year", None)
    if school_id:
        plans = TuitionPlan.objects.filter(school_id=school_id, is_active=True)
        if academic_year:
            plans = plans.filter(academic_year__name=str(academic_year))
        annual_amount_cents = plans.order_by("-annual_amount_cents").values_list(
            "annual_amount_cents", flat=True
        ).first()
        if annual_amount_cents:
            return Decimal(annual_amount_cents) / Decimal("100")

    return DEFAULT_TUITION_ESTIMATE


def calculate_need_index_breakdown(application: FinancialAidApplication) -> dict[str, float]:
    """Return the weighted CROWN need-index breakdown on a 0..100 scale."""
    household_income = _to_decimal(getattr(application, "household_income", None), default=Decimal("0"))
    tuition_estimate = _resolve_tuition_estimate(application)

    if tuition_estimate > 0 and household_income > 0:
        income_ratio = household_income / tuition_estimate
        income_factor = _clamp_unit(Decimal("1") - income_ratio)
    else:
        income_factor = NEUTRAL_INCOME_FACTOR

    total_dependents = _to_int(
        getattr(application, "total_dependents", None),
        default=max(_to_int(getattr(application, "household_size", None), default=0), 0),
    )
    dependents_in_school = _to_int(
        getattr(application, "dependents_in_school", None),
        default=total_dependents,
    )
    if total_dependents > 0:
        dependents_factor = _clamp_unit(Decimal(dependents_in_school) / Decimal(total_dependents))
    else:
        dependents_factor = 0.0

    special_points = 0
    if bool(getattr(application, "is_pastor_family", False)):
        special_points += 40
    if bool(getattr(application, "has_medical_hardship", False)):
        special_points += 30
    if bool(getattr(application, "has_financial_hardship", False)):
        special_points += 30
    other_special = getattr(application, "other_special_circumstances", "") or getattr(
        application, "has_other_hardship", False
    )
    if other_special:
        special_points += 10
    special_circumstances_factor = _clamp_unit(Decimal(special_points) / Decimal("100"))

    previous_aid_amount = _to_decimal(getattr(application, "previous_aid_amount", None), default=Decimal("0"))
    previous_tuition = _to_decimal(getattr(application, "previous_tuition", None), default=Decimal("0"))
    adjustment_factor = _clamp_unit(getattr(application, "prior_aid_adjustment_factor", 1.0))
    if previous_aid_amount > 0 and previous_tuition > 0:
        prior_factor = _clamp_unit(
            (previous_aid_amount / previous_tuition) * Decimal(str(adjustment_factor))
        )
    else:
        prior_factor = RETURNING_FAMILY_FACTOR

    weighted_score = (
        (Decimal(str(income_factor)) * Decimal("0.40"))
        + (Decimal(str(dependents_factor)) * Decimal("0.25"))
        + (Decimal(str(special_circumstances_factor)) * Decimal("0.20"))
        + (Decimal(str(prior_factor)) * Decimal("0.15"))
    ) * Decimal("100")
    need_index = float(weighted_score.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    need_index = max(0.0, min(100.0, need_index))

    return {
        "income_factor": round(income_factor, 4),
        "dependents_factor": round(dependents_factor, 4),
        "special_circumstances_factor": round(special_circumstances_factor, 4),
        "prior_aid_history_factor": round(prior_factor, 4),
        "need_index": need_index,
    }


def calculate_need_index(application: FinancialAidApplication) -> float:
    """Return the official CROWN weighted need index on a 0..100 scale."""
    return calculate_need_index_breakdown(application)["need_index"]
