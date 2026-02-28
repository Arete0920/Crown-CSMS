from django.urls import path

from .wizard_api import wizard_configure, wizard_lock, wizard_snapshot, wizard_status

urlpatterns = [
    path("wizard/status/", wizard_status, name="finance_setup_wizard_status"),
    path("wizard/configure/", wizard_configure, name="finance_setup_wizard_configure"),
    path("wizard/lock/", wizard_lock, name="finance_setup_wizard_lock"),
    path("wizard/snapshot/", wizard_snapshot, name="finance_setup_wizard_snapshot"),
]
