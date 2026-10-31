"""Offline financial aid read-model tests. No Django fixtures are needed."""
import pytest
from crown_api.dashboards.financial_aid_live import (
    summarize_financial_aid_rows, FinancialAidDashboardIntegrityError,
)

S = '11111111-1111-1111-1111-111111111111'
T = '22222222-2222-2222-2222-222222222222'
Y = '33333333-3333-3333-3333-333333333333'
F = '44444444-4444-4444-4444-444444444444'
STUDENT = '55555555-5555-5555-5555-555555555555'

def app(status='SUBMITTED', **changes):
    row = dict(family_id=F, family__school_id=S, academic_year__school_id=S, status=status)
    row.update(changes)
    return row

def award(status='ACCEPTED', cents=12500, **changes):
    row = dict(student_id=STUDENT, student__school_id=S, student__family_id=F,
               student__family__school_id=S, academic_year__school_id=S,
               aid_application_id='linked', aid_application__school_id=S,
               aid_application__academic_year_id=Y, aid_application__family_id=F,
               decision_status=status, awarded_cents=cents, ledger_entry_id=None)
    row.update(changes)
    return row

def facts(apps=None, awards=None):
    return summarize_financial_aid_rows(school_id=S, year_id=Y,
        applications=[app()] if apps is None else apps,
        awards=[award()] if awards is None else awards)

def test_family_application_and_award_record_units():
    apps = [app(s) for s in ['DRAFT','SUBMITTED','UNDER_REVIEW','NEEDS_INFO',
                             'APPROVED','DENIED','WITHDRAWN']]
    x = facts(apps, [award(), award('OFFERED', 5000), award('DECLINED', 3000)])
    assert x == dict(submitted_applications=5, submitted_families=1,
        applications_requiring_review=3, accepted_award_records=1,
        accepted_award_face_value_cents=12500, accepted_without_ledger_count=1)

def test_empty_records_report_real_zeroes():
    assert facts([],[]) == dict(submitted_applications=0, submitted_families=0,
        applications_requiring_review=0, accepted_award_records=0,
        accepted_award_face_value_cents=0, accepted_without_ledger_count=0)

def test_multiple_awards_do_not_inflate_family_count():
    x = facts([app()], [award(), award(cents=7500)])
    assert (x['accepted_award_records'], x['accepted_award_face_value_cents'], x['submitted_families']) == (2, 20000, 1)

@pytest.mark.parametrize('changed', [
    {'family__school_id': T}, {'academic_year__school_id': T},
    {'family_id': None}, {'status': 'INVENTED'}])
def test_inconsistent_application_is_not_counted(changed):
    with pytest.raises(FinancialAidDashboardIntegrityError):
        facts([app(**changed)], [])

@pytest.mark.parametrize('changed', [
    {'student__school_id': T}, {'student__family__school_id': T},
    {'academic_year__school_id': T}, {'aid_application__school_id': T},
    {'aid_application__academic_year_id': T}, {'aid_application__family_id': T},
    {'decision_status': 'INVENTED'}, {'awarded_cents': -1},
    {'awarded_cents': None}, {'student__family_id': None}])
def test_inconsistent_award_is_not_counted(changed):
    with pytest.raises(FinancialAidDashboardIntegrityError):
        facts([], [award(**changed)])

def test_accepted_award_must_have_positive_face_value():
    with pytest.raises(FinancialAidDashboardIntegrityError):
        facts([], [award(cents=0)])

def test_legacy_unlinked_application_is_allowed_but_not_certified_as_cash():
    assert facts([], [award(aid_application_id=None)])['accepted_without_ledger_count'] == 1

def test_linked_legacy_ledger_requires_exact_record_match():
    fields = dict(ledger_entry_id='entry', ledger_entry__school_id=S,
        ledger_entry__academic_year_id=Y, ledger_entry__student_id=STUDENT,
        ledger_entry__family_id=F, ledger_entry__amount_cents=-12500,
        ledger_entry__is_reversal=False)
    assert facts([], [award(**fields)])['accepted_without_ledger_count'] == 0

@pytest.mark.parametrize('bad', [
    {'ledger_entry__school_id': T}, {'ledger_entry__academic_year_id': T},
    {'ledger_entry__student_id': T}, {'ledger_entry__family_id': T},
    {'ledger_entry__amount_cents': -12499}, {'ledger_entry__is_reversal': True}])
def test_inconsistent_legacy_ledger_fails_closed(bad):
    fields = dict(ledger_entry_id='entry', ledger_entry__school_id=S,
        ledger_entry__academic_year_id=Y, ledger_entry__student_id=STUDENT,
        ledger_entry__family_id=F, ledger_entry__amount_cents=-12500,
        ledger_entry__is_reversal=False)
    fields.update(bad)
    with pytest.raises(FinancialAidDashboardIntegrityError):
        facts([], [award(**fields)])
