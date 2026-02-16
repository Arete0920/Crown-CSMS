from django.urls import path
from .views import compuwerx_webhook

urlpatterns = [
    path("compuwerx/webhook/", compuwerx_webhook, name="compuwerx-webhook"),
]
