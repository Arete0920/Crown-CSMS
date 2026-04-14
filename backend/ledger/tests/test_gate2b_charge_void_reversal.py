import uuid
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from core.models import School
from households.models import Household
from ledger.models import Charge, LedgerAccount
from journal.models import JournalEntry, GLAccount


pytestmark = pytest.mark.django_db

TEST_AUTH_SECRET = "testpass"


def test_void_charge_creates_single_reversal_entry():
    User = get_user_model()
    user = User.objects.create_user(username="t", password=TEST_AUTH_SECRET)

    school = School.objects.create(name="Heritage")
    
    # Create household and ledger account (required by Charge model)
    household = Household.objects.create(school_id=school.id, name="Test Household")
    ledger_account = LedgerAccount.objects.create(school_id=school.id, household=household)
    
    # Ensure GL accounts exist (signals will create them, but explicit is clearer)
    ar = GLAccount.objects.create(school=school, code="1100", name="Accounts Receivable", account_type="ASSET")
    revenue = GLAccount.objects.create(school=school, code="4000", name="Tuition Revenue", account_type="REVENUE")

    # Create charge (existing signals should post the JE with reference_type="charge")
    ch = Charge.objects.create(
        school_id=school.id,
        account=ledger_account,
        description="Tuition charge",
        amount=Decimal("100.00"),
        is_void=False,
    )

    original = JournalEntry.objects.filter(
        school=school,
        reference_type="charge",
        reference_id=ch.id,
    ).first()
    assert original is not None, "Expected original JE to be posted for charge"
    original_lines = list(original.lines.all())
    assert len(original_lines) > 0

    # Void it (should create reversal once)
    ch.is_void = True
    ch.save()

    original.refresh_from_db()
    reversal = getattr(original, "reversal_entry", None)
    assert reversal is not None, "Expected reversal_entry to exist"
    assert reversal.reversal_of_id == original.id

    # Lines are swapped DR/CR
    rev_lines = list(reversal.lines.all())
    assert len(rev_lines) == len(original_lines)

    orig_pairs = sorted([(l.account_id, str(l.debit), str(l.credit)) for l in original_lines])
    rev_pairs = sorted([(l.account_id, str(l.debit), str(l.credit)) for l in rev_lines])

    # For each original line, reversal should have debit=orig.credit and credit=orig.debit
    expected_rev = sorted([(a, c, d) for (a, d, c) in orig_pairs])
    assert rev_pairs == expected_rev

    # Idempotent: saving again doesn't create another reversal
    ch.save()
    assert JournalEntry.objects.filter(reversal_of=original).count() == 1

