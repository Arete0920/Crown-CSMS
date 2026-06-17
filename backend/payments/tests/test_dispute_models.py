import uuid
from decimal import Decimal

import pytest
from django.db import IntegrityError

from core.models import School
from payments.models import (
    GatewayProvider,
    ProviderDispute,
    ProviderDisputeStatus,
    ProviderPayoutBatch,
    ProviderPayoutEntry,
)


pytestmark = pytest.mark.django_db


def test_dispute_and_payout_models_persist_expected_fields():
    school = School.objects.create(name="Payment Provider School")

    dispute = ProviderDispute.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        dispute_id=f"disp_{uuid.uuid4().hex[:12]}",
        provider_payment_id="pay_123",
        amount=Decimal("12.34"),
        currency="USD",
        reason="fraudulent",
        status=ProviderDisputeStatus.OPEN,
        payload={"sample": True},
    )

    batch = ProviderPayoutBatch.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        payout_id=f"po_{uuid.uuid4().hex[:12]}",
        status="paid",
        gross_amount=Decimal("50.00"),
        fee_amount=Decimal("1.00"),
        net_amount=Decimal("49.00"),
        currency="USD",
        expected_payment_count=1,
        payload={"raw": "batch"},
    )

    entry = ProviderPayoutEntry.objects.create(
        batch=batch,
        provider_payment_id="pay_123",
        gross_amount=Decimal("50.00"),
        fee_amount=Decimal("1.00"),
        net_amount=Decimal("49.00"),
        currency="USD",
        payload={"raw": "entry"},
    )

    assert dispute.dispute_id.startswith("disp_")
    assert batch.payout_id.startswith("po_")
    assert entry.batch_id == batch.id


def test_dispute_id_is_unique():
    school = School.objects.create(name="Payment Provider School")
    dispute_id = f"disp_{uuid.uuid4().hex[:12]}"

    ProviderDispute.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        dispute_id=dispute_id,
    )

    with pytest.raises(IntegrityError):
        ProviderDispute.objects.create(
            school_id=school.id,
            provider=GatewayProvider.COMPUWERX,
            dispute_id=dispute_id,
        )
