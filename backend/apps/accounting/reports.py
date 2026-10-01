from decimal import Decimal

from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.accounting.models.institutional import AccountingDimension, Budget
from journal.models import JournalLine

ZERO = Decimal("0.00")


def _normal_balance(account_type: str, debit: Decimal, credit: Decimal) -> Decimal:
    if account_type in {"LIABILITY", "EQUITY", "REVENUE"}:
        return credit - debit
    return debit - credit


def trial_balance(*, school_id, start_date=None, end_date=None):
    qs = JournalLine.objects.filter(entry__school_id=school_id)
    if start_date:
        qs = qs.filter(entry__posting_date__gte=start_date)
    if end_date:
        qs = qs.filter(entry__posting_date__lte=end_date)
    rows = (
        qs.values("account_id", "account__code", "account__name", "account__account_type")
        .annotate(
            debit=Coalesce(Sum("debit"), ZERO),
            credit=Coalesce(Sum("credit"), ZERO),
        )
        .order_by("account__code")
    )
    result = []
    total_debit = ZERO
    total_credit = ZERO
    for row in rows:
        debit = row["debit"] or ZERO
        credit = row["credit"] or ZERO
        total_debit += debit
        total_credit += credit
        result.append(
            {
                "account_id": row["account_id"],
                "code": row["account__code"],
                "name": row["account__name"],
                "account_type": row["account__account_type"],
                "debit": debit,
                "credit": credit,
                "balance": _normal_balance(row["account__account_type"], debit, credit),
            }
        )
    return {
        "rows": result,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "balanced": total_debit == total_credit,
    }


def income_statement(*, school_id, start_date, end_date):
    tb = trial_balance(school_id=school_id, start_date=start_date, end_date=end_date)
    revenue = [row for row in tb["rows"] if row["account_type"] == "REVENUE"]
    expenses = [row for row in tb["rows"] if row["account_type"] == "EXPENSE"]
    revenue_total = sum((row["balance"] for row in revenue), ZERO)
    expense_total = sum((row["balance"] for row in expenses), ZERO)
    return {
        "start_date": start_date,
        "end_date": end_date,
        "revenue": revenue,
        "expenses": expenses,
        "revenue_total": revenue_total,
        "expense_total": expense_total,
        "net_income": revenue_total - expense_total,
    }


def balance_sheet(*, school_id, as_of):
    tb = trial_balance(school_id=school_id, end_date=as_of)
    assets = [row for row in tb["rows"] if row["account_type"] == "ASSET"]
    liabilities = [row for row in tb["rows"] if row["account_type"] == "LIABILITY"]
    equity = [row for row in tb["rows"] if row["account_type"] == "EQUITY"]
    revenue = [row for row in tb["rows"] if row["account_type"] == "REVENUE"]
    expenses = [row for row in tb["rows"] if row["account_type"] == "EXPENSE"]
    asset_total = sum((row["balance"] for row in assets), ZERO)
    liability_total = sum((row["balance"] for row in liabilities), ZERO)
    equity_total = sum((row["balance"] for row in equity), ZERO)
    current_earnings = (
        sum((row["balance"] for row in revenue), ZERO)
        - sum((row["balance"] for row in expenses), ZERO)
    )
    return {
        "as_of": as_of,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "asset_total": asset_total,
        "liability_total": liability_total,
        "equity_total": equity_total,
        "current_earnings": current_earnings,
        "difference": asset_total - liability_total - equity_total - current_earnings,
    }


def _apply_dimension_filter(qs, dimension):
    if not dimension:
        return qs
    lookup = {
        AccountingDimension.Kind.DEPARTMENT: "department_code",
        AccountingDimension.Kind.PROGRAM: "program_code",
        AccountingDimension.Kind.CAMPUS: "campus_code",
        AccountingDimension.Kind.PROJECT: "project_code",
    }[dimension.kind]
    return qs.filter(**{lookup: dimension.code})


def budget_vs_actual(*, budget: Budget):
    rows = []
    budget_total = ZERO
    actual_total = ZERO
    for line in budget.lines.select_related("account", "fund", "dimension").order_by("account__code"):
        qs = JournalLine.objects.filter(
            entry__school_id=budget.tenant_id,
            entry__posting_date__gte=budget.fiscal_start,
            entry__posting_date__lte=budget.fiscal_end,
            account=line.account,
        )
        if line.fund_id:
            qs = qs.filter(fund_code=line.fund.code)
        qs = _apply_dimension_filter(qs, line.dimension)
        totals = qs.aggregate(
            debit=Coalesce(Sum("debit"), ZERO),
            credit=Coalesce(Sum("credit"), ZERO),
        )
        actual = _normal_balance(line.account.account_type, totals["debit"], totals["credit"])
        budget_total += line.amount
        actual_total += actual
        rows.append(
            {
                "budget_line_id": line.id,
                "account_code": line.account.code,
                "account_name": line.account.name,
                "fund_code": line.fund.code if line.fund else "",
                "dimension_kind": line.dimension.kind if line.dimension else "",
                "dimension_code": line.dimension.code if line.dimension else "",
                "budget": line.amount,
                "actual": actual,
                "variance": line.amount - actual,
            }
        )
    return {
        "budget_id": budget.id,
        "budget_total": budget_total,
        "actual_total": actual_total,
        "variance": budget_total - actual_total,
        "rows": rows,
    }
