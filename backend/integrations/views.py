from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST


@csrf_exempt
@require_POST
def compuwerx_webhook(request):
    return JsonResponse(
        {
            "ok": False,
            "error": "legacy_compuwerx_webhook_retired",
            "detail": "Use /api/v1/payments/webhooks/compuwerx/.",
        },
        status=410,
    )
