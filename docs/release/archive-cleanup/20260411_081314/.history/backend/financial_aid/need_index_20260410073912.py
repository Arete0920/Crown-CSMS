from __future__ import annotations

from decimal import Decimal

from .models import FinancialAidApplication


def calculate_need_index(application: FinancialAidApplication) -> int:
    """Return a simple 0..100 need score using existing application fields only."""
    income = Decimal(str(application.household_income or "0"))
    household_size = max(int(application.household_size or 1), 1)
    income_per_person = income / Decimal(household_size)

    if income_per_person <= Decimal("10000"):
        base_score = 95
    elif income_per_person <= Decimal("15000"):
        base_score = 85
    elif income_per_person <= Decimal("20000"):
        base_score = 75
    elif income_per_person <= Decimal("30000"):
        base_score = 60
    elif income_per_person <= Decimal("45000"):
        base_score = 40
    else:
        base_score = 20

    if household_size >= 7:
        base_score += 10
    elif household_size >= 5:
        base_score += 5

    return max(0, min(int(base_score), 100))
