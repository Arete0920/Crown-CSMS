"""Verify the *content* of a declined award's reversal, not merely its count.

Offline ORM-double tests. Full Django/PostgreSQL integration is a separate gate.
"""
from sys import modules
from types import ModuleType, SimpleNamespace
import pytest

from crown_api.dashboards.financial_aid_live import (
    FinancialAidDashboardIntegrityError, financial_aid_live_payload,
)

SCHOOL = '11111111-1111-1111-1111-111111111111'
OTHER = '22222222-2222-2222-2222-222222222222'
YEAR = '33333333-3333-3333-3333-333333333333'
FAMILY = '44444444-4444-4444-4444-444444444444'
STUDENT = '55555555-5555-5555-5555-555555555555'
ACCOUNT = '66666666-6666-6666-6666-666666666666'
ORIGINAL = '77777777-7777-7777-7777-777777777777'


def declined_award():
    return dict(student_id=STUDENT, student__school_id=SCHOOL,
        student__family_id=FAMILY, student__family__school_id=SCHOOL,
        academic_year__school_id=SCHOOL, aid_application_id=None,
        decision_status='DECLINED', awarded_cents=12500,
        ledger_entry_id=ORIGINAL, ledger_entry__school_id=SCHOOL,
        ledger_entry__academic_year_id=YEAR,
        ledger_entry__student_id=STUDENT, ledger_entry__family_id=FAMILY,
        ledger_entry__account__school_id=SCHOOL,
        ledger_entry__account__code='AID', ledger_entry__account_id=ACCOUNT,
        ledger_entry__source='AID_AWARD', ledger_entry__is_reversal=False,
        ledger_entry__reversal_of_id=None, ledger_entry__amount_cents=-12500,
        ledger_reversal_count=1)


def reversal_row(**kwargs):
    r = dict(reversal_of_id=ORIGINAL, school_id=SCHOOL, family_id=FAMILY,
       student_id=STUDENT, academic_year_id=YEAR, account_id=ACCOUNT,
       amount_cents=12500, source='AID_AWARD', is_reversal=True)
    r.update(kwargs)
    return r


class Query:
    def __init__(self, rows, name, log):
        self.rows = rows
        self.name = name
        self.log = log

    def filter(self, **kwargs):
        self.log.append((self.name, 'filter', kwargs))
        return self

    def values_list(self, *args, **kwargs):
        return self

    def annotate(self, **kwargs):
        return self

    def values(self, *args):
        self.log.append((self.name, 'values', args))
        return self

    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, key):
        return self.rows[key]


@pytest.fixture
def fake_orm(monkeypatch):
    state = {'years': [YEAR], 'apps': [], 'awards': [declined_award()],
             'reversals': [reversal_row()]}
    calls = []

    def put(name, **members):
        m = ModuleType(name)
        m.__dict__.update(members)
        monkeypatch.setitem(modules, name, m)

    class FakeCount:
        def __init__(self, field, distinct=False):
            self.field = field
            self.distinct = distinct

    put('aid', __path__=[])
    put('aid.models', AidApplication=SimpleNamespace(objects=Query(state['apps'], 'app', calls)),
        AidAward=SimpleNamespace(objects=Query(state['awards'], 'award', calls)))
    put('core', __path__=[])
    put('core.models', AcademicYear=SimpleNamespace(objects=Query(state['years'], 'year', calls)),
        LedgerEntry=SimpleNamespace(objects=Query(state['reversals'], 'reversal', calls)))
    put('django', __path__=[])
    put('django.db', __path__=[])
    put('django.db.models', Count=FakeCount)

    def metric(label, value, secondary=None):
        return {'label': label, 'value': str(value)}
    def alert(title, level, text):
        return {'title': title, 'level': level, 'secondary': text}
    def payload(**kwargs):
        return kwargs
    put('crown_api.dashboards.payload_contract', metric=metric, alert=alert,
        build_dashboard_payload=payload)
    return state, calls


def test_exact_reversal_keeps_declined_award_out_of_live_totals(fake_orm):
    state, calls = fake_orm
    result = financial_aid_live_payload(SCHOOL)
    assert result['meta']['accepted_award_records'] == 0
    assert result['meta']['accepted_award_face_value_cents'] == 0
    assert any(name == 'reversal' and op == 'filter' and set(args['reversal_of_id__in']) == {ORIGINAL}
               for name, op, args in calls if op == 'filter')
    assert all('family_name' not in str(x) for x in (result['meta'], result['metrics']))


@pytest.mark.parametrize('changed', [
    {'school_id': OTHER}, {'family_id': OTHER}, {'student_id': OTHER},
    {'academic_year_id': OTHER}, {'account_id': OTHER}, {'source': 'PAYMENT'},
    {'amount_cents': -12500}, {'amount_cents': 12300},
    {'is_reversal': False}, {'reversal_of_id': OTHER},
])
def test_malformed_reversal_fails_closed(fake_orm, changed):
    state, _ = fake_orm
    state['reversals'][0].update(changed)
    with pytest.raises(FinancialAidDashboardIntegrityError):
        financial_aid_live_payload(SCHOOL)


def test_no_reversal_fails_even_if_aggregate_count_says_one(fake_orm):
    state, _ = fake_orm
    state['reversals'].clear()
    with pytest.raises(FinancialAidDashboardIntegrityError):
        financial_aid_live_payload(SCHOOL)


def test_two_reversals_fail_even_if_aggregate_count_says_one(fake_orm):
    state, _ = fake_orm
    state['reversals'].append(reversal_row())
    with pytest.raises(FinancialAidDashboardIntegrityError):
        financial_aid_live_payload(SCHOOL)


def test_accepted_unreversed_ledger_skips_reversal_query(fake_orm):
    state, calls = fake_orm
    state['awards'][0]['decision_status'] = 'ACCEPTED'
    state['awards'][0]['ledger_reversal_count'] = 0
    result = financial_aid_live_payload(SCHOOL)
    assert result['meta']['accepted_award_records'] == 1
    assert result['meta']['accepted_award_face_value_cents'] == 12500
    assert not any(name == 'reversal' for name, *_ in calls)
