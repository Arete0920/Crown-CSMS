from django.urls import path
from .views import compuwerx_webhook
from .oneroster import oneroster_export_bundle

urlpatterns = [
    # Legacy endpoint is intentionally retired. Canonical signed webhook is
    # /api/v1/payments/webhooks/compuwerx/.
    path("compuwerx/webhook/", compuwerx_webhook, name="compuwerx-webhook"),
    path("oneroster/export/", oneroster_export_bundle, name="oneroster-export"),
]
