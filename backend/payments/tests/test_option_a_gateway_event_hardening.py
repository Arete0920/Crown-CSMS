from decimal import Decimal
from unittest.mock import patch

import pytest

from core.models import School, UserAccount
from finance.models import FinancePayment, PaymentStatus, Processor
from households.models import Household
from payments.models import (
    CanonicalPaymentStatus,
    GatewayEvent,
    GatewayEventStatus,
    GatewayProvider,
    Payment,
    PaymentIntentRecord,
    PaymentSupportException,
    ProviderDispute,
    SavedPaymentMethod,
)
from payments.services import (
    SettlementAllocationRequired,
    UnmatchedPaymentError,
    _apply_refund,
    process_gateway_event_safely,
)

pytestmark = pytest.mark.django_db


def _school_user():
    school = School.objects.create(name="Payments Option A")
    user = UserAccount.objects.create_user(
        username="payer",
        email="payer@example.com",
        password="pass",
        school=school,
    )
    return school, user


def _payment(school, user, *, provider_id="pay_123", status=PaymentStatus.PENDING):
    return FinancePayment.objects.create(
        school=school,
        payer_user=user,
        amount_cents=10_000,
        processor=Processor.COMPUWERX,
        processor_payment_id=provider_id,
        status=status,
    )


def _intent(
    school,
    *,
    metadata=None,
    provider_payment_id="pay_123",
    client_reference_id="client_123",
):
    return PaymentIntentRecord.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        amount=Decimal("100.00"),
        currency="USD",
        client_reference_id=client_reference_id,
        provider_intent_id="intent_123",
        provider_payment_id=provider_payment_id,
        metadata=metadata or {},
    )


def _event(school, *, status="settled", payment_id="pay_123"):
    return GatewayEvent.objects.create(
        school_id=school.id,
        provider=GatewayProvider.COMPUWERX,
        event_id=f"evt_{status}_{payment_id}",
        event_type="payment.updated",
        provider_intent_id="intent_123",
        provider_payment_id=payment_id,
        raw_body="{}",
        payload={
            "intent_id": "intent_123",
            "payment_id": payment_id,
            "status": status,
        },
    )


def test_settlement_without_explicit_allocations_fails_and_records_exception():
    school, user = _school_user()
    payment = _payment(school, user)
    _intent(school, metadata={"finance_payment_id": payment.id})
    event = _event(school)

    with pytest.raises(SettlementAllocationRequired):
        process_gateway_event_safely(event)

    payment.refresh_from_db()
    event.refresh_from_db()
    assert payment.status == PaymentStatus.PENDING
    assert event.status == GatewayEventStatus.FAILED
    assert not Payment.objects.filter(finance_payment_id=payment.id).exists()
    assert PaymentSupportException.objects.filter(
        school_id=school.id,
        gateway_event_id=event.id,
        category="gateway_event_processing",
    ).exists()


def test_provider_intent_or_client_reference_is_not_overloaded_as_payment_id():
    school, user = _school_user()
    _payment(school, user, provider_id="client_123")
    _intent(
        school,
        provider_payment_id="pay_real",
        client_reference_id="client_123",
    )
    event = _event(school, payment_id="pay_real")

    with pytest.raises(UnmatchedPaymentError):
        process_gateway_event_safely(event)
    event.refresh_from_db()
    assert event.status == GatewayEventStatus.FAILED


def test_settlement_event_creates_canonical_payment_and_routes_to_authority():
    school, user = _school_user()
    legacy_payment = _payment(school, user)
    _intent(
        school,
        metadata={
            "finance_payment_id": legacy_payment.id,
            "allocations": [{"obligation_id": 41, "amount_cents": 6_000}],
        },
    )
    event = _event(school)

    with patch("payments.services.settle_payment") as settle:
        process_gateway_event_safely(event)

    canonical = Payment.objects.get(finance_payment_id=legacy_payment.id)
    assert canonical.amount_cents == legacy_payment.amount_cents
    assert canonical.provider == GatewayProvider.COMPUWERX
    assert canonical.provider_intent_id == "intent_123"
    assert canonical.provider_payment_id == "pay_123"
    assert canonical.idempotency_key.startswith("gateway_intent:")
    assert settle.call_count == 1
    assert settle.call_args.kwargs["payment"].pk == canonical.pk
    assert settle.call_args.kwargs["allocations_payload"] == [
        {"obligation_id": 41, "amount_cents": 6_000}
    ]
    event.refresh_from_db()
    assert event.status == GatewayEventStatus.PROCESSED


def test_refund_requires_prior_canonical_settlement_reconciliation():
    school, user = _school_user()
    legacy_payment = _payment(school, user, status=PaymentStatus.SETTLED)
    intent = _intent(school, metadata={"finance_payment_id": legacy_payment.id})
    event = _event(school, status="refunded")

    with pytest.raises(UnmatchedPaymentError, match="settlement reconciliation"):
        _apply_refund(
            event,
            intent,
            {"refund_amount": "10.00"},
            provider=GatewayProvider.COMPUWERX,
        )


def test_refund_routes_through_canonical_authority_and_preserves_provider_refund_id():
    school, user = _school_user()
    legacy_payment = _payment(school, user, status=PaymentStatus.SETTLED)
    intent = _intent(school, metadata={"finance_payment_id": legacy_payment.id})
    event = _event(school, status="refunded")
    Payment.objects.create(
        school_id=school.id,
        finance_payment_id=legacy_payment.id,
        amount_cents=legacy_payment.amount_cents,
        currency="USD",
        status=CanonicalPaymentStatus.SETTLED,
        provider=GatewayProvider.COMPUWERX,
        provider_intent_id="intent_123",
        provider_payment_id="pay_123",
        idempotency_key="canonical-existing",
    )
    refund_sentinel = object()

    with (
        patch("payments.services.request_refund", return_value=refund_sentinel) as request,
        patch("payments.services.settle_refund") as settle,
    ):
        _apply_refund(
            event,
            intent,
            {"refund_amount": "10.00", "refund_id": "refund_real_123"},
            provider=GatewayProvider.COMPUWERX,
        )

    assert request.call_count == 1
    assert request.call_args.kwargs["amount_cents"] == 1_000
    assert request.call_args.kwargs["provider"] == GatewayProvider.COMPUWERX
    assert request.call_args.kwargs["idempotency_key"] == (
        f"gateway_refund_event:{GatewayProvider.COMPUWERX}:{event.event_id}"
    )
    assert settle.call_count == 1
    assert settle.call_args.kwargs["refund"] is refund_sentinel
    assert settle.call_args.kwargs["provider"] == GatewayProvider.COMPUWERX
    assert settle.call_args.kwargs["provider_refund_id"] == "refund_real_123"


def _event_with_payload(school, event_type, event_id, payload):
    return GatewayEvent.objects.create(
        school_id=school.id if school is not None else None,
        provider=GatewayProvider.COMPUWERX,
        event_id=event_id,
        event_type=event_type,
        raw_body="{}",
        payload=payload,
    )


def test_gateway_intent_lookup_does_not_cross_school_boundary():
    school, user = _school_user()
    other_school = School.objects.create(name="Other payment tenant")
    payment = _payment(school, user)
    intent = _intent(school, metadata={"finance_payment_id": payment.id})
    event = _event_with_payload(
        other_school, "payment.updated", "other-school-settled",
        {"intent_id": intent.provider_intent_id, "payment_id": "pay_123", "status": "settled"},
    )

    process_gateway_event_safely(event)

    intent.refresh_from_db()
    payment.refresh_from_db()
    event.refresh_from_db()
    assert intent.status == "created"
    assert payment.status == PaymentStatus.PENDING
    assert not Payment.objects.filter(school_id=school.id, finance_payment_id=payment.id).exists()
    assert event.status == GatewayEventStatus.IGNORED


def test_gateway_event_rejects_claimed_school_different_from_verified_ownership():
    school, user = _school_user()
    another_school = School.objects.create(name="Another school")
    event = _event_with_payload(
        school, "payment.updated", "forged-school-in-payload",
        {
            "intent_id": "forged-intent",
            "status": "settled",
            "metadata": {"school_id": str(another_school.id)},
        },
    )

    with pytest.raises(UnmatchedPaymentError, match="conflicts with verified school"):
        process_gateway_event_safely(event)

    event.refresh_from_db()
    assert event.status == GatewayEventStatus.FAILED
    assert PaymentSupportException.objects.filter(
        school_id=school.id, gateway_event_id=event.id
    ).exists()


def test_gateway_event_without_verified_school_cannot_mutate_financial_state():
    event = _event_with_payload(
        None, "payment.updated", "unowned-provider-event",
        {"intent_id": "unknown", "status": "settled"},
    )

    with pytest.raises(UnmatchedPaymentError, match="verified school ownership"):
        process_gateway_event_safely(event)

    event.refresh_from_db()
    assert event.status == GatewayEventStatus.FAILED
    assert not PaymentSupportException.objects.filter(gateway_event_id=event.id).exists()


def test_saved_method_event_requires_locally_owned_household():
    school, _ = _school_user()
    other_school = School.objects.create(name="Other saved-method tenant")
    household = Household.objects.create(school_id=other_school.id, name="Other family")
    event = _event_with_payload(
        school, "payment_method.saved", "wrong-school-household",
        {"payment_method_id": "method-foreign", "metadata": {"household_id": str(household.id)}},
    )

    with pytest.raises(UnmatchedPaymentError, match="household is not owned"):
        process_gateway_event_safely(event)

    assert not SavedPaymentMethod.objects.filter(provider_method_id="method-foreign").exists()


def test_saved_method_event_cannot_overwrite_another_school_record():
    school, _ = _school_user()
    other_school = School.objects.create(name="Other method owner")
    own_household = Household.objects.create(school_id=school.id, name="Home family")
    other_household = Household.objects.create(school_id=other_school.id, name="Other family")
    method = SavedPaymentMethod.objects.create(
        school_id=other_school.id,
        household_id=other_household.id,
        provider=GatewayProvider.COMPUWERX,
        provider_method_id="provider-method-shared",
        last4="1234",
    )
    event = _event_with_payload(
        school, "payment_method.saved", "method-cross-school-replay",
        {
            "payment_method_id": "provider-method-shared",
            "last4": "9999",
            "metadata": {"household_id": str(own_household.id)},
        },
    )

    with pytest.raises(UnmatchedPaymentError, match="existing ownership"):
        process_gateway_event_safely(event)

    method.refresh_from_db()
    assert method.school_id == other_school.id
    assert method.last4 == "1234"


def test_saved_method_event_for_owned_household_retains_valid_processing():
    school, _ = _school_user()
    household = Household.objects.create(school_id=school.id, name="Owned payment family")
    event = _event_with_payload(
        school, "payment_method.saved", "method-owned-valid",
        {
            "payment_method_id": "provider-method-owned",
            "last4": "4321",
            "metadata": {"household_id": str(household.id)},
        },
    )

    process_gateway_event_safely(event)

    saved = SavedPaymentMethod.objects.get(provider_method_id="provider-method-owned")
    assert saved.school_id == school.id
    assert saved.household_id == household.id
    assert saved.last4 == "4321"


def test_detach_event_does_not_change_method_owned_by_another_school():
    school, _ = _school_user()
    other_school = School.objects.create(name="Detached-method owner")
    household = Household.objects.create(school_id=other_school.id, name="Other payment family")
    method = SavedPaymentMethod.objects.create(
        school_id=other_school.id,
        household_id=household.id,
        provider=GatewayProvider.COMPUWERX,
        provider_method_id="method-to-protect",
        is_active=True,
    )
    event = _event_with_payload(
        school, "payment_method.detached", "foreign-detach-event",
        {"payment_method_id": "method-to-protect"},
    )

    process_gateway_event_safely(event)

    method.refresh_from_db()
    assert method.is_active


def test_dispute_event_does_not_overwrite_another_school_dispute():
    school, _ = _school_user()
    other_school = School.objects.create(name="Original dispute owner")
    existing = ProviderDispute.objects.create(
        school_id=other_school.id,
        provider=GatewayProvider.COMPUWERX,
        dispute_id="dispute-shared",
        status="open",
    )
    event = _event_with_payload(
        school, "dispute.opened", "dispute-cross-school-open",
        {"dispute_id": "dispute-shared", "status": "lost", "amount": "50.00"},
    )

    with pytest.raises(UnmatchedPaymentError, match="existing ownership"):
        process_gateway_event_safely(event)

    existing.refresh_from_db()
    assert existing.school_id == other_school.id
    assert existing.status == "open"


def test_dispute_status_event_does_not_change_another_school():
    school, _ = _school_user()
    other_school = School.objects.create(name="Foreign dispute owner")
    existing = ProviderDispute.objects.create(
        school_id=other_school.id,
        provider=GatewayProvider.COMPUWERX,
        dispute_id="foreign-dispute-status",
        status="open",
    )
    event = _event_with_payload(
        school, "dispute.updated", "foreign-dispute-update",
        {"dispute_id": "foreign-dispute-status", "status": "lost"},
    )

    with pytest.raises(UnmatchedPaymentError, match="conflicts with verified ownership"):
        process_gateway_event_safely(event)

    existing.refresh_from_db()
    event.refresh_from_db()
    assert existing.status == "open"
    assert event.status == GatewayEventStatus.FAILED
    assert PaymentSupportException.objects.filter(
        school_id=school.id, gateway_event_id=event.id,
        category="gateway_event_processing",
    ).exists()


def test_dispute_event_rejects_foreign_household_metadata():
    school, _ = _school_user()
    other_school = School.objects.create(name="Dispute foreign family")
    household = Household.objects.create(school_id=other_school.id, name="Outside household")
    event = _event_with_payload(
        school, "dispute.opened", "dispute-foreign-household",
        {
            "dispute_id": "fresh-dispute",
            "amount": "40.00",
            "metadata": {"household_id": str(household.id)},
        },
    )

    with pytest.raises(UnmatchedPaymentError, match="household is not owned"):
        process_gateway_event_safely(event)

    assert not ProviderDispute.objects.filter(dispute_id="fresh-dispute").exists()


@pytest.mark.parametrize("field,reference", [
    ("intent_id", "foreign-intent-ref"),
    ("payment_id", "foreign-payment-ref"),
])
def test_dispute_rejects_provider_reference_owned_by_another_school(field, reference):
    school, _ = _school_user()
    other = School.objects.create(name="Other gateway owner")
    PaymentIntentRecord.objects.create(
        school_id=other.id,
        provider=GatewayProvider.COMPUWERX,
        client_reference_id="other-gateway-client",
        provider_intent_id="foreign-intent-ref",
        provider_payment_id="foreign-payment-ref",
        amount=Decimal("10.00"),
    )
    event = _event_with_payload(
        school, "dispute.opened", f"foreign-dispute-{field}",
        {"dispute_id": f"dispute-{field}", field: reference},
    )
    with pytest.raises(UnmatchedPaymentError, match="another school"):
        process_gateway_event_safely(event)
    assert not ProviderDispute.objects.filter(dispute_id=f"dispute-{field}").exists()


def test_dispute_accepts_owned_provider_references():
    school, _ = _school_user()
    _intent(school, client_reference_id="owned-dispute-client")
    event = _event_with_payload(
        school, "dispute.opened", "owned-gateway-dispute",
        {"dispute_id": "owned-dispute", "intent_id": "intent_123",
         "payment_id": "pay_123", "amount": "10.00"},
    )
    process_gateway_event_safely(event)
    dispute = ProviderDispute.objects.get(dispute_id="owned-dispute")
    assert dispute.school_id == school.id
