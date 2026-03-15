from payments.models import PaymentExceptionSeverity, PaymentSupportException


def record_payment_exception(
    *,
    school_id,
    provider: str,
    category: str,
    message: str,
    payload: dict | None = None,
    severity: str = PaymentExceptionSeverity.ERROR,
    gateway_event_id: int | None = None,
    payment_intent_record_id: int | None = None,
    dispute_id: int | None = None,
    payout_batch_id: int | None = None,
    household_id=None,
) -> PaymentSupportException:
    return PaymentSupportException.objects.create(
        school_id=school_id,
        provider=provider,
        category=category,
        severity=severity,
        message=message,
        payload=payload or {},
        gateway_event_id=gateway_event_id,
        payment_intent_record_id=payment_intent_record_id,
        dispute_id=dispute_id,
        payout_batch_id=payout_batch_id,
        household_id=household_id,
    )
