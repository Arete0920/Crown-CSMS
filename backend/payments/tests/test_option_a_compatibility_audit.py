import pytest

from core.models import School, UserAccount
from finance.models import FinancePayment, PaymentStatus, Processor
from payments.authority_services import create_payment
from payments.compatibility_audit import audit_payment_compatibility


pytestmark = pytest.mark.django_db


def _user(username):
    return UserAccount.objects.create_user(
        username=username,
        password="pass",
        email=f"{username}@test.example.com",
    )


def test_compatibility_audit_passes_for_linked_matching_payment():
    school = School.objects.create(name="Compatibility Audit Pass")
    payer = _user("compat_audit_pass")
    legacy = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=12_500,
        currency="USD",
        processor=Processor.MANUAL,
        status=PaymentStatus.PENDING,
    )
    create_payment(
        school_id=school.id,
        finance_payment_id=legacy.id,
        amount_cents=12_500,
        currency="USD",
        idempotency_key="compat-audit-pass-1",
        created_by=payer,
    )

    result = audit_payment_compatibility(school_id=school.id)

    assert result.ok
    assert result.checked_payments == 1
    assert result.mismatches == []
    assert result.orphan_legacy_payments == []


def test_compatibility_audit_blocks_unmigrated_legacy_payment():
    school = School.objects.create(name="Compatibility Audit Orphan")
    payer = _user("compat_audit_orphan")
    orphan = FinancePayment.objects.create(
        school=school,
        payer_user=payer,
        amount_cents=5_000,
        currency="USD",
        processor=Processor.MANUAL,
        status=PaymentStatus.PENDING,
    )

    result = audit_payment_compatibility(school_id=school.id)

    assert not result.ok
    assert result.orphan_legacy_payments == [orphan.id]
