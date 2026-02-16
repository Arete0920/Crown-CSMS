import json
from django.db import IntegrityError, transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from ledger.models import Payment
from .models import WebhookEvent


@csrf_exempt
@require_POST
def compuwerx_webhook(request):
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return JsonResponse({"ok": False, "error": "invalid_json"}, status=400)

    event_id = (data.get("event_id") or "").strip()
    event_type = (data.get("type") or "").strip()
    payment_id = data.get("payment_id")

    if not event_id or not event_type:
        return JsonResponse({"ok": False, "error": "missing_event_fields"}, status=400)

    # Idempotency gate
    try:
        with transaction.atomic():
            evt = WebhookEvent.objects.create(
                provider="compuwerx",
                event_id=event_id,
                payload=data,
            )
    except IntegrityError:
        # replay: do nothing
        return JsonResponse({"ok": True, "replayed": True}, status=200)

    # Minimal routing for Gate 2C proof
    if event_type == "payment.voided":
        if not payment_id:
            return JsonResponse({"ok": False, "error": "missing_payment_id"}, status=400)

        p = Payment.objects.filter(pk=payment_id).first()
        if not p:
            return JsonResponse({"ok": False, "error": "payment_not_found"}, status=404)

        # This triggers the pre_save/post_save reversal path
        if not p.is_void:
            p.is_void = True
            p.save(update_fields=["is_void"])

    evt.processed_at = timezone.now()
    evt.save(update_fields=["processed_at"])
    return JsonResponse({"ok": True}, status=200)
