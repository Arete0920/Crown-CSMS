"""Financial facts preserve authority, school ownership and journal atomicity."""
from decimal import Decimal
import uuid
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import Client

from core.models import School
from households.models import Household
from journal.models import JournalEntry
from ledger.models import Charge, Credit, LedgerAccount, Payment
from ledger.tests.factories import grant_finance_authority

pytestmark = pytest.mark.django_db


@pytest.fixture
def account():
    school = School.objects.create(name="Financial fact boundary")
    household = Household.objects.create(school_id=school.id, name="Synthetic household")
    return LedgerAccount.objects.create(school_id=school.id, household=household)


def fact(model, account):
    values = dict(school_id=account.school_id, account=account, amount=Decimal("100.00"))
    if model is Charge:
        values['description'] = 'Synthetic tuition'
    else:
        values.update(source='ADJUSTMENT' if model is Credit else 'EXTERNAL', reference=str(uuid.uuid4()))
    return model.objects.create(**values)


@pytest.mark.parametrize('model', [Charge, Credit, Payment])
def test_queryset_and_bulk_changes_cannot_bypass_financial_fact_guards(model, account):
    row = fact(model, account)
    for operation in (
        lambda: model.objects.filter(pk=row.pk).update(amount=Decimal('1.00')),
        lambda: model.objects.filter(pk=row.pk).update(is_void=True),
        lambda: model.objects.bulk_update([row], ['amount']),
        lambda: model.objects.filter(pk=row.pk).delete(),
        lambda: row.delete(),
        lambda: model.objects.bulk_create([row]),
    ):
        with pytest.raises(ValidationError):
            operation()
    row.refresh_from_db()
    assert row.amount == Decimal('100.00') and not row.is_void


@pytest.mark.parametrize('model', [Charge, Payment])
def test_journal_posting_failure_rolls_back_financial_fact(model, account):
    with patch('ledger.signals.post_journal_entry', side_effect=RuntimeError('Synthetic posting failure')):
        with pytest.raises(RuntimeError):
            fact(model, account)
    assert model.objects.count() == 0
    assert JournalEntry.objects.count() == 0


def test_forged_adding_state_cannot_overwrite_existing_financial_facts(account):
    row = fact(Charge, account)
    forged = Charge(pk=row.pk, school_id=account.school_id, account=account,
                    amount=Decimal('1.00'), description='Tampered')
    assert forged._state.adding
    with pytest.raises(ValidationError):
        forged.save()
    row.refresh_from_db()
    assert row.amount == Decimal('100.00')


def test_cross_school_financial_fact_rejected_before_posting(account):
    other = School.objects.create(name='Other financial school')
    with pytest.raises(ValidationError):
        Charge.objects.create(school_id=other.id, account=account, amount=Decimal('100.00'), description='Wrong school')
    assert Charge.objects.count() == 0
    assert JournalEntry.objects.count() == 0


@pytest.mark.parametrize('path', ['charges/{id}/void/', 'payments/{id}/void/'])
def test_plain_authenticated_user_cannot_void_financial_facts(account, path):
    model = Charge if path.startswith('charges') else Payment
    row = fact(model, account)
    school = School.objects.get(pk=account.school_id)
    user = get_user_model().objects.create_user(username=f'no-finance-{uuid.uuid4()}', school=school)
    client = Client()
    client.force_login(user)
    response = client.post('/api/v1/ledger/' + path.format(id=row.id), HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 403
    row.refresh_from_db()
    assert not row.is_void
    grant_finance_authority(user, school.id)
    response = client.post('/api/v1/ledger/' + path.format(id=row.id), HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200
    row.refresh_from_db()
    assert row.is_void


@pytest.mark.parametrize('method,path', [
    ('get', 'invariants/'),
    ('get', 'charges/open/'),
    ('get', 'accounts/{id}/'),
    ('get', 'accounts/{id}/balance/'),
    ('get', 'accounts/{id}/statement/'),
    ('post', 'accounts/ensure/'),
    ('post', 'charges/'),
    ('post', 'payments/'),
    ('post', 'payments/{id}/allocate/'),
])
def test_all_finance_surfaces_reject_authenticated_users_without_finance_grants(account, method, path):
    school = School.objects.get(pk=account.school_id)
    user = get_user_model().objects.create_user(username=f'no-grant-{uuid.uuid4()}', school=school)
    client = Client()
    client.force_login(user)
    response = getattr(client, method)('/api/v1/ledger/' + path.format(id=account.id),
                                      HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 403
    assert Charge.objects.count() == Payment.objects.count() == 0


@pytest.mark.parametrize('model', [Charge, Credit, Payment])
def test_voided_facts_cannot_be_reactivated_without_new_posting(model, account):
    row = fact(model, account)
    row.is_void = True
    row.save(update_fields=['is_void'])
    entries = JournalEntry.objects.count()
    row.is_void = False
    with pytest.raises(ValidationError):
        row.save(update_fields=['is_void'])
    row.refresh_from_db()
    assert row.is_void
    assert JournalEntry.objects.count() == entries


@pytest.mark.parametrize('model', [Charge, Payment])
def test_reversal_posting_failure_rolls_back_void(model, account):
    row = fact(model, account)
    entries = JournalEntry.objects.count()
    row.is_void = True
    with patch('ledger.signals.create_reversal_entry', side_effect=RuntimeError('Synthetic reversal failure')):
        with pytest.raises(RuntimeError):
            row.save(update_fields=['is_void'])
    row.refresh_from_db()
    assert not row.is_void
    assert JournalEntry.objects.count() == entries


def test_void_endpoints_do_not_swallow_unexpected_failures():
    """Unexpected persistence faults must not be mislabeled as 404s."""
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "api.py").read_text(encoding="utf-8-sig")
    assert "except (Charge.DoesNotExist, Exception):" not in source
    assert "except (Payment.DoesNotExist, Exception):" not in source
    assert "except (ValueError, Charge.DoesNotExist):" in source
    assert "except (ValueError, Payment.DoesNotExist):" in source
