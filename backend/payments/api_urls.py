from django.urls import path

from .account_api import household_finance_summary, household_payment_history
from .api_views import create_payment_intent, payment_intent_status
from .bank_recon_api import (
    auto_match_payouts,
    bank_statement_imports_list,
    manual_match_payout,
    payout_bank_matches_list,
    unmatched_bank_entries_list,
    upload_bank_statement_csv,
)
from .disputes_api import dispute_action_create, dispute_detail
from .exceptions_api import (
    payment_exception_ignore,
    payment_exception_retry,
    payment_exceptions_list,
)
from .export_api import household_statement_csv, payment_receipt_html
from .methods_api import (
    create_payment_method_setup,
    detach_payment_method,
    list_saved_payment_methods,
    set_default_payment_method,
)
from .ops_api import disputes_list, payout_batch_detail, payout_batches_list

urlpatterns = [
    path("intents/", create_payment_intent, name="payments-create-intent"),
    path(
        "intents/<str:intent_id>/status/",
        payment_intent_status,
        name="payments-intent-status",
    ),
    path(
        "accounts/<uuid:household_id>/summary/",
        household_finance_summary,
        name="payments-household-summary",
    ),
    path(
        "accounts/<uuid:household_id>/history/",
        household_payment_history,
        name="payments-household-history",
    ),
    path(
        "accounts/<uuid:household_id>/statement.csv",
        household_statement_csv,
        name="payments-household-statement-csv",
    ),
    path(
        "receipts/<uuid:payment_id>/",
        payment_receipt_html,
        name="payments-receipt-html",
    ),
    path(
        "accounts/<uuid:household_id>/methods/",
        list_saved_payment_methods,
        name="payments-methods-list",
    ),
    path(
        "accounts/<uuid:household_id>/methods/setup/",
        create_payment_method_setup,
        name="payments-methods-setup",
    ),
    path(
        "accounts/<uuid:household_id>/methods/<int:method_id>/default/",
        set_default_payment_method,
        name="payments-methods-default",
    ),
    path(
        "accounts/<uuid:household_id>/methods/<int:method_id>/",
        detach_payment_method,
        name="payments-methods-detach",
    ),
    path("disputes/", disputes_list, name="payments-disputes-list"),
    path("disputes/<int:dispute_id>/", dispute_detail, name="payments-dispute-detail"),
    path(
        "disputes/<int:dispute_id>/actions/",
        dispute_action_create,
        name="payments-dispute-action-create",
    ),
    path("payout-batches/", payout_batches_list, name="payments-payout-batches-list"),
    path(
        "payout-batches/<int:batch_id>/",
        payout_batch_detail,
        name="payments-payout-batch-detail",
    ),
    path("exceptions/", payment_exceptions_list, name="payments-exceptions-list"),
    path(
        "exceptions/<int:exception_id>/retry/",
        payment_exception_retry,
        name="payments-exception-retry",
    ),
    path(
        "exceptions/<int:exception_id>/ignore/",
        payment_exception_ignore,
        name="payments-exception-ignore",
    ),
    path(
        "bank/imports/", bank_statement_imports_list, name="payments-bank-imports-list"
    ),
    path(
        "bank/imports/upload/",
        upload_bank_statement_csv,
        name="payments-bank-import-upload",
    ),
    path(
        "bank/unmatched-entries/",
        unmatched_bank_entries_list,
        name="payments-bank-unmatched-entries",
    ),
    path(
        "bank/payout-matches/",
        payout_bank_matches_list,
        name="payments-bank-payout-matches-list",
    ),
    path(
        "bank/payout-matches/auto/",
        auto_match_payouts,
        name="payments-bank-payout-auto-match",
    ),
    path(
        "bank/payout-matches/manual/",
        manual_match_payout,
        name="payments-bank-payout-manual-match",
    ),
]
