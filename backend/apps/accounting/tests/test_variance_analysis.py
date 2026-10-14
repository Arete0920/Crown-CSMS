"""Pure arithmetic tests; no database or external services required."""

from decimal import Decimal

from apps.accounting.variance_analysis import explain_variance


def test_expense_over_budget_is_unfavorable():
    outcome = explain_variance(account_type="EXPENSE", budget=Decimal("100.00"), actual=Decimal("125.00"))
    assert outcome == {
        "deviation_amount": Decimal("25.00"),
        "deviation_percent": Decimal("25.00"),
        "favorability": "UNFAVORABLE",
    }


def test_revenue_over_budget_is_favorable():
    outcome = explain_variance(account_type="REVENUE", budget=Decimal("100.00"), actual=Decimal("112.345"))
    assert outcome["deviation_percent"] == Decimal("12.35")
    assert outcome["favorability"] == "FAVORABLE"


def test_expense_below_budget_is_favorable():
    outcome = explain_variance(account_type="EXPENSE", budget=Decimal("100.00"), actual=Decimal("90.00"))
    assert outcome["deviation_amount"] == Decimal("-10.00")
    assert outcome["favorability"] == "FAVORABLE"


def test_revenue_below_budget_is_unfavorable():
    outcome = explain_variance(account_type="REVENUE", budget=Decimal("100.00"), actual=Decimal("90.00"))
    assert outcome["favorability"] == "UNFAVORABLE"


def test_zero_budget_does_not_divide_by_zero_or_claim_a_percent():
    outcome = explain_variance(account_type="EXPENSE", budget=Decimal("0.00"), actual=Decimal("10.00"))
    assert outcome["deviation_percent"] is None
    assert outcome["favorability"] == "UNFAVORABLE"


def test_non_operating_account_has_no_favorability_classification():
    outcome = explain_variance(account_type="ASSET", budget=Decimal("20.00"), actual=Decimal("30.00"))
    assert outcome["favorability"] == "NOT_ASSESSED"


def test_exact_budget_has_no_deviation():
    outcome = explain_variance(account_type="REVENUE", budget=Decimal("200.00"), actual=Decimal("200.00"))
    assert outcome["deviation_amount"] == Decimal("0.00")
    assert outcome["deviation_percent"] == Decimal("0.00")
    assert outcome["favorability"] == "ON_TARGET"


def test_negative_revenue_actual_preserves_sign():
    outcome = explain_variance(account_type="REVENUE", budget=Decimal("100.00"), actual=Decimal("-25.00"))
    assert outcome["deviation_percent"] == Decimal("-125.00")
    assert outcome["favorability"] == "UNFAVORABLE"
