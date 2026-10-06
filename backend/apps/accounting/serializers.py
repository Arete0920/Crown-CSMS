from rest_framework import serializers


class VendorSerializer(serializers.Serializer):
    id = serializers.CharField()
    code = serializers.CharField()
    legal_name = serializers.CharField()
    display_name = serializers.CharField(allow_blank=True)
    email = serializers.CharField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    payment_terms_days = serializers.IntegerField()
    default_expense_account_id = serializers.CharField(allow_null=True)
    active = serializers.BooleanField()


class VendorListSerializer(serializers.Serializer):
    results = VendorSerializer(many=True)


class FundSerializer(serializers.Serializer):
    id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    restriction = serializers.CharField()
    active = serializers.BooleanField()


class FundListSerializer(serializers.Serializer):
    results = FundSerializer(many=True)


class AccountingDimensionSerializer(serializers.Serializer):
    id = serializers.CharField()
    kind = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    active = serializers.BooleanField()


class AccountingDimensionListSerializer(serializers.Serializer):
    results = AccountingDimensionSerializer(many=True)


class PurchaseOrderLineSerializer(serializers.Serializer):
    id = serializers.CharField()
    description = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=18, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=18, decimal_places=2)
    line_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    account_id = serializers.CharField()
    fund_id = serializers.CharField(allow_null=True)
    dimension_id = serializers.CharField(allow_null=True)


class PurchaseOrderSerializer(serializers.Serializer):
    id = serializers.CharField()
    vendor_id = serializers.CharField()
    number = serializers.CharField()
    status = serializers.CharField()
    ordered_on = serializers.DateField()
    expected_on = serializers.DateField(allow_null=True)
    currency = serializers.CharField()
    memo = serializers.CharField(allow_blank=True)
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    approved_by = serializers.CharField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    lines = PurchaseOrderLineSerializer(many=True)


class PurchaseOrderListSerializer(serializers.Serializer):
    results = PurchaseOrderSerializer(many=True)


class PayableBillLineSerializer(serializers.Serializer):
    id = serializers.CharField()
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    expense_account_id = serializers.CharField()
    fund_id = serializers.CharField(allow_null=True)
    dimension_id = serializers.CharField(allow_null=True)


class PayableBillSerializer(serializers.Serializer):
    id = serializers.CharField()
    vendor_id = serializers.CharField()
    purchase_order_id = serializers.CharField(allow_null=True)
    bill_number = serializers.CharField()
    bill_date = serializers.DateField()
    due_date = serializers.DateField()
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    currency = serializers.CharField()
    liability_account_id = serializers.CharField()
    status = serializers.CharField()
    memo = serializers.CharField(allow_blank=True)
    journal_entry_id = serializers.CharField(allow_null=True)
    approved_by = serializers.CharField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    posted_at = serializers.DateTimeField(allow_null=True)
    lines = PayableBillLineSerializer(many=True)


class PayableBillListSerializer(serializers.Serializer):
    results = PayableBillSerializer(many=True)


class BudgetLineSerializer(serializers.Serializer):
    id = serializers.CharField()
    account_id = serializers.CharField()
    fund_id = serializers.CharField(allow_null=True)
    dimension_id = serializers.CharField(allow_null=True)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    note = serializers.CharField(allow_blank=True)


class BudgetSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    fiscal_start = serializers.DateField()
    fiscal_end = serializers.DateField()
    status = serializers.CharField()
    approved_by = serializers.CharField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    lines = BudgetLineSerializer(many=True)


class BudgetListSerializer(serializers.Serializer):
    results = BudgetSerializer(many=True)


class TrialBalanceRowSerializer(serializers.Serializer):
    account_id = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    account_type = serializers.CharField()
    debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    balance = serializers.DecimalField(max_digits=18, decimal_places=2)


class TrialBalanceSerializer(serializers.Serializer):
    rows = TrialBalanceRowSerializer(many=True)
    total_debit = serializers.DecimalField(max_digits=18, decimal_places=2)
    total_credit = serializers.DecimalField(max_digits=18, decimal_places=2)
    balanced = serializers.BooleanField()


class IncomeStatementSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    revenue = TrialBalanceRowSerializer(many=True)
    expenses = TrialBalanceRowSerializer(many=True)
    revenue_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    expense_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    net_income = serializers.DecimalField(max_digits=18, decimal_places=2)


class BalanceSheetSerializer(serializers.Serializer):
    as_of = serializers.DateField()
    assets = TrialBalanceRowSerializer(many=True)
    liabilities = TrialBalanceRowSerializer(many=True)
    equity = TrialBalanceRowSerializer(many=True)
    asset_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    liability_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    equity_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    current_earnings = serializers.DecimalField(max_digits=18, decimal_places=2)
    difference = serializers.DecimalField(max_digits=18, decimal_places=2)


class BudgetVarianceRowSerializer(serializers.Serializer):
    budget_line_id = serializers.CharField()
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    fund_code = serializers.CharField(allow_blank=True)
    dimension_kind = serializers.CharField(allow_blank=True)
    dimension_code = serializers.CharField(allow_blank=True)
    budget = serializers.DecimalField(max_digits=18, decimal_places=2)
    actual = serializers.DecimalField(max_digits=18, decimal_places=2)
    variance = serializers.DecimalField(max_digits=18, decimal_places=2)


class BudgetVarianceSerializer(serializers.Serializer):
    budget_id = serializers.CharField()
    budget_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    actual_total = serializers.DecimalField(max_digits=18, decimal_places=2)
    variance = serializers.DecimalField(max_digits=18, decimal_places=2)
    rows = BudgetVarianceRowSerializer(many=True)
