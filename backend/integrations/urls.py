from django.urls import path
from .oneroster import oneroster_export_bundle
from .sds_v21 import sds_v21_export

urlpatterns = [
    path("oneroster/export/", oneroster_export_bundle, name="oneroster-export"),
    path("microsoft/sds-v2.1/export/", sds_v21_export, name="microsoft-sds-v21-export"),
]
