import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.accounting.models import JournalEntry, LedgerAccount, LedgerEntry


pytestmark = pytest.mark.django_db


def _journal(tenant_id):
    return JournalEntry.objects.create(
        tenant_id=tenant_id,
        correlation_id=uuid.uuid4(),
        source_system="test",
        created_by=uuid.uuid4(),
        description="Initial journal",
    )


def _account(tenant_id, code="1000"):
    return LedgerAccount.objects.create(
        tenant_id=tenant_id,
        code=code,
        name="Cash",
        account_type="ASSET",
    )


def _ledger_entry():
    tenant_id = uuid.uuid4()
    return LedgerEntry(
        tenant_id=tenant_id,
        journal_entry=_journal(tenant_id),
        account=_account(tenant_id),
        entry_type="DEBIT",
        amount=Decimal("10.00"),
        currency="USD",
    )


def test_initial_ledger_entry_save_succeeds_with_uuid_default_primary_key():
    entry = _ledger_entry()

    entry.save()

    assert LedgerEntry.objects.filter(pk=entry.pk).exists()


def test_same_tenant_ledger_entry_accepts_string_tenant_id():
    tenant_id = uuid.uuid4()
    entry = LedgerEntry.objects.create(
        tenant_id=str(tenant_id),
        journal_entry=_journal(tenant_id),
        account=_account(tenant_id),
        entry_type="DEBIT",
        amount=Decimal("10.00"),
        currency="USD",
    )

    entry.refresh_from_db()
    assert entry.tenant_id == tenant_id


@pytest.mark.parametrize("relation", ["journal_entry", "account"])
def test_cross_tenant_ledger_entry_relation_is_rejected(relation):
    tenant_id = uuid.uuid4()
    other_tenant_id = uuid.uuid4()
    values = {
        "tenant_id": tenant_id,
        "journal_entry": _journal(tenant_id),
        "account": _account(tenant_id),
        "entry_type": "DEBIT",
        "amount": Decimal("10.00"),
        "currency": "USD",
    }
    values[relation] = {
        "journal_entry": _journal(other_tenant_id),
        "account": _account(other_tenant_id, code="2000"),
    }[relation]

    with pytest.raises(ValidationError, match="same tenant"):
        LedgerEntry.objects.create(**values)

    assert LedgerEntry.objects.count() == 0


def test_existing_ledger_entry_cannot_be_saved_again():
    entry = _ledger_entry()
    entry.save()
    entry.amount = Decimal("20.00")

    with pytest.raises(ValidationError, match="immutable"):
        entry.save()

    entry.refresh_from_db()
    assert entry.amount == Decimal("10.00")


def test_ledger_entry_delete_is_rejected():
    entry = _ledger_entry()
    entry.save()

    with pytest.raises(ValidationError, match="cannot be deleted"):
        entry.delete()

    assert LedgerEntry.objects.filter(pk=entry.pk).exists()
