from rest_framework import serializers


class DetailErrorSerializer(serializers.Serializer):
    detail = serializers.JSONField()


class VendorSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    legal_name = serializers.CharField()
    display_name = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    phone = serializers.CharField(allow_blank=True)
    payment_terms_days = serializers.IntegerField()
    default_expense_account_id = serializers.UUIDField(allow_null=True)
    active = serializers.BooleanField()


class VendorListSerializer(serializers.Serializer):
    results = VendorSerializer(many=True)


class VendorCreateSerializer(serializers.Serializer):
    code = serializers.CharField()
    legal_name = serializers.CharField()
    display_name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    payment_terms_days = serializers.IntegerField(required=False, min_value=0)
    default_expense_account_id = serializers.UUIDField(required=False, allow_null=True)


class FundSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    restriction = serializers.CharField()
    active = serializers.BooleanField()


class FundListSerializer(serializers.Serializer):
    results = FundSerializer(many=True)


class FundCreateSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    restriction = serializers.CharField(required=False)


class DimensionSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    kind = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()
    active = serializers.BooleanField()


class DimensionListSerializer(serializers.Serializer):
    results = DimensionSerializer(many=True)


class DimensionCreateSerializer(serializers.Serializer):
    kind = serializers.CharField()
    code = serializers.CharField()
    name = serializers.CharField()


class PurchaseOrderLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    quantity = serializers.FloatField()
    unit_cost = serializers.FloatField()
    line_total = serializers.FloatField()
    account_id = serializers.UUIDField()
    fund_id = serializers.UUIDField(allow_null=True)
    dimension_id = serializers.UUIDField(allow_null=True)


class PurchaseOrderSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    vendor_id = serializers.UUIDField()
    number = serializers.CharField()
    status = serializers.CharField()
    ordered_on = serializers.DateField()
    expected_on = serializers.DateField(allow_null=True)
    currency = serializers.CharField()
    memo = serializers.CharField(allow_blank=True)
    total_amount = serializers.FloatField()
    approved_by = serializers.UUIDField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    lines = PurchaseOrderLineSerializer(many=True)


class PurchaseOrderListSerializer(serializers.Serializer):
    results = PurchaseOrderSerializer(many=True)


class PurchaseOrderLineCreateSerializer(serializers.Serializer):
    description = serializers.CharField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=2)
    account_id = serializers.UUIDField()
    fund_id = serializers.UUIDField(required=False, allow_null=True)
    dimension_id = serializers.UUIDField(required=False, allow_null=True)


class PurchaseOrderCreateSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField()
    number = serializers.CharField()
    ordered_on = serializers.DateField(required=False)
    expected_on = serializers.DateField(required=False, allow_null=True)
    currency = serializers.CharField(required=False)
    memo = serializers.CharField(required=False, allow_blank=True)
    lines = PurchaseOrderLineCreateSerializer(many=True)


class PayableBillLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    description = serializers.CharField()
    amount = serializers.FloatField()
    expense_account_id = serializers.UUIDField()
    fund_id = serializers.UUIDField(allow_null=True)
    dimension_id = serializers.UUIDField(allow_null=True)


class PayableBillSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    vendor_id = serializers.UUIDField()
    purchase_order_id = serializers.UUIDField(allow_null=True)
    bill_number = serializers.CharField()
    bill_date = serializers.DateField()
    due_date = serializers.DateField()
    total_amount = serializers.FloatField()
    currency = serializers.CharField()
    liability_account_id = serializers.UUIDField()
    status = serializers.CharField()
    memo = serializers.CharField(allow_blank=True)
    journal_entry_id = serializers.UUIDField(allow_null=True)
    approved_by = serializers.UUIDField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    posted_at = serializers.DateTimeField(allow_null=True)
    lines = PayableBillLineSerializer(many=True)


class PayableBillListSerializer(serializers.Serializer):
    results = PayableBillSerializer(many=True)


class PayableBillLineCreateSerializer(serializers.Serializer):
    description = serializers.CharField()
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    expense_account_id = serializers.UUIDField()
    fund_id = serializers.UUIDField(required=False, allow_null=True)
    dimension_id = serializers.UUIDField(required=False, allow_null=True)


class PayableBillCreateSerializer(serializers.Serializer):
    vendor_id = serializers.UUIDField()
    purchase_order_id = serializers.UUIDField(required=False, allow_null=True)
    bill_number = serializers.CharField()
    bill_date = serializers.DateField()
    due_date = serializers.DateField()
    total_amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    currency = serializers.CharField(required=False)
    liability_account_id = serializers.UUIDField()
    memo = serializers.CharField(required=False, allow_blank=True)
    lines = PayableBillLineCreateSerializer(many=True)


class PayableBillActionSerializer(serializers.Serializer):
    reason = serializers.CharField(required=False, allow_blank=True)


class BudgetLineSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    account_id = serializers.UUIDField()
    fund_id = serializers.UUIDField(allow_null=True)
    dimension_id = serializers.UUIDField(allow_null=True)
    amount = serializers.FloatField()
    note = serializers.CharField(allow_blank=True)


class BudgetSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    fiscal_start = serializers.DateField()
    fiscal_end = serializers.DateField()
    status = serializers.CharField()
    approved_by = serializers.UUIDField(allow_null=True)
    approved_at = serializers.DateTimeField(allow_null=True)
    total_amount = serializers.FloatField()
    lines = BudgetLineSerializer(many=True)


class BudgetListSerializer(serializers.Serializer):
    results = BudgetSerializer(many=True)


class BudgetLineCreateSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    fund_id = serializers.UUIDField(required=False, allow_null=True)
    dimension_id = serializers.UUIDField(required=False, allow_null=True)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    note = serializers.CharField(required=False, allow_blank=True)


class BudgetCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    fiscal_start = serializers.DateField()
    fiscal_end = serializers.DateField()
    lines = BudgetLineCreateSerializer(many=True)


class LedgerBalanceRowSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    account_type = serializers.CharField()
    debit = serializers.FloatField()
    credit = serializers.FloatField()
    balance = serializers.FloatField()


class TrialBalanceSerializer(serializers.Serializer):
    rows = LedgerBalanceRowSerializer(many=True)
    total_debit = serializers.FloatField()
    total_credit = serializers.FloatField()
    balanced = serializers.BooleanField()


class IncomeStatementSerializer(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    revenue = LedgerBalanceRowSerializer(many=True)
    expenses = LedgerBalanceRowSerializer(many=True)
    revenue_total = serializers.FloatField()
    expense_total = serializers.FloatField()
    net_income = serializers.FloatField()


class BalanceSheetSerializer(serializers.Serializer):
    as_of = serializers.DateField()
    assets = LedgerBalanceRowSerializer(many=True)
    liabilities = LedgerBalanceRowSerializer(many=True)
    equity = LedgerBalanceRowSerializer(many=True)
    asset_total = serializers.FloatField()
    liability_total = serializers.FloatField()
    equity_total = serializers.FloatField()
    current_earnings = serializers.FloatField()
    difference = serializers.FloatField()


class BudgetVarianceRowSerializer(serializers.Serializer):
    budget_line_id = serializers.UUIDField()
    account_code = serializers.CharField()
    account_name = serializers.CharField()
    fund_code = serializers.CharField(allow_blank=True)
    dimension_kind = serializers.CharField(allow_blank=True)
    dimension_code = serializers.CharField(allow_blank=True)
    budget = serializers.FloatField()
    actual = serializers.FloatField()
    variance = serializers.FloatField()


class BudgetVarianceSerializer(serializers.Serializer):
    budget_id = serializers.UUIDField()
    budget_total = serializers.FloatField()
    actual_total = serializers.FloatField()
    variance = serializers.FloatField()
    rows = BudgetVarianceRowSerializer(many=True)
