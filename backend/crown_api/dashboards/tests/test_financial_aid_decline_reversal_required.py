"""A declined award with a legacy posting must retain exactly one verified reversal."""

import pytest

from crown_api.dashboards.financial_aid_live import (
    FinancialAidDashboardIntegrityError,
    summarize_financial_aid_rows,
)

SCHOOL = "11111111-1111-1111-1111-111111111111"
YEAR = "22222222-2222-2222-2222-222222222222"
FAMILY = "33333333-3333-3333-3333-333333333333"
STUDENT = "44444444-4444-4444-4444-444444444444"


def declined_award(*, linked=True, reversals=0, validated=False):
    return dict(
        student_id=STUDENT,
        student__school_id=SCHOOL,
        student__family_id=FAMILY,
        student__family__school_id=SCHOOL,
        academic_year__school_id=SCHOOL,
        aid_application_id=None,
        decision_status="DECLINED",
        awarded_cents=12500,
        ledger_entry_id="legacy-posting" if linked else None,
        ledger_entry__school_id=SCHOOL,
        ledger_entry__academic_year_id=YEAR,
        ledger_entry__student_id=STUDENT,
        ledger_entry__family_id=FAMILY,
        ledger_entry__amount_cents=-12500,
        ledger_entry__is_reversal=False,
        ledger_entry__source="AID_AWARD",
        ledger_entry__account__school_id=SCHOOL,
        ledger_entry__account__code="AID",
        ledger_entry__reversal_of_id=None,
        ledger_reversal_count=reversals,
        ledger_reversal_validated=validated,
    )


def summarize(row):
    return summarize_financial_aid_rows(
        school_id=SCHOOL, year_id=YEAR, applications=[], awards=[row]
    )


def test_declined_legacy_posting_without_reversal_requires_reconciliation():
    with pytest.raises(FinancialAidDashboardIntegrityError):
        summarize(declined_award(linked=True, reversals=0))


def test_declined_unposted_award_needs_no_legacy_reversal():
    result = summarize(declined_award(linked=False, reversals=0))
    assert result["accepted_award_records"] == 0
    assert result["accepted_award_face_value_cents"] == 0


def test_declined_legacy_posting_with_one_reversal_is_excluded_from_totals():
    result = summarize(declined_award(linked=True, reversals=1, validated=True))
    assert result["accepted_award_records"] == 0
    assert result["accepted_award_face_value_cents"] == 0


def test_declined_legacy_posting_with_multiple_reversals_requires_reconciliation():
    with pytest.raises(FinancialAidDashboardIntegrityError):
        summarize(declined_award(linked=True, reversals=2))


def test_count_only_is_not_sufficient_for_decline_reconciliation():
    with pytest.raises(FinancialAidDashboardIntegrityError):
        summarize(declined_award(linked=True, reversals=1, validated=False))
