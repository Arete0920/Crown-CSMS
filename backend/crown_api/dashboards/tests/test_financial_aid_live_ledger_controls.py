import pytest
from crown_api.dashboards.financial_aid_live import summarize_financial_aid_rows, FinancialAidDashboardIntegrityError

S='11111111-1111-1111-1111-111111111111'
T='22222222-2222-2222-2222-222222222222'
Y='33333333-3333-3333-3333-333333333333'
F='44444444-4444-4444-4444-444444444444'
U='55555555-5555-5555-5555-555555555555'

def award(status='ACCEPTED', **kw):
    row=dict(student_id=U,student__school_id=S,student__family_id=F,
      student__family__school_id=S,academic_year__school_id=S,
      aid_application_id=None,decision_status=status,awarded_cents=12500,
      ledger_entry_id='entry',ledger_entry__school_id=S,
      ledger_entry__academic_year_id=Y,ledger_entry__student_id=U,
      ledger_entry__family_id=F,ledger_entry__amount_cents=-12500,
      ledger_entry__is_reversal=False,ledger_entry__source='AID_AWARD',
      ledger_entry__account__school_id=S,ledger_entry__account__code='AID',
      ledger_entry__reversal_of_id=None,ledger_reversal_count=0)
    row.update(kw)
    return row

def summarize(row):
    return summarize_financial_aid_rows(school_id=S,year_id=Y,applications=[],awards=[row])

def test_valid_posted_accepted_award():
    x=summarize(award())
    assert (x['accepted_award_records'],x['accepted_award_face_value_cents'],x['accepted_without_ledger_count'])==(1,12500,0)

def test_declined_award_reversal_not_accepted_value():
    x=summarize(award('DECLINED',ledger_reversal_count=1))
    assert x['accepted_award_records']==0
    assert x['accepted_award_face_value_cents']==0

@pytest.mark.parametrize('bad',[
    {'ledger_entry__source':'TUITION_SET'}, {'ledger_entry__source':None},
    {'ledger_entry__account__school_id':T}, {'ledger_entry__account__code':'FEES'},
    {'ledger_entry__reversal_of_id':'prior'}, {'ledger_reversal_count':1},
    {'ledger_reversal_count':2}, {'ledger_reversal_count':None},
    {'ledger_entry__amount_cents':-12499}, {'ledger_entry__family_id':T},
    {'decision_status':'OFFERED'}, {'awarded_cents':True},
])
def test_inconsistent_posting_fails_closed(bad):
    with pytest.raises(FinancialAidDashboardIntegrityError):
        summarize(award(**bad))
