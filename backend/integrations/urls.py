from django.urls import path
from .oneroster import oneroster_export_bundle

urlpatterns = [
    path("oneroster/export/", oneroster_export_bundle, name="oneroster-export"),
]
