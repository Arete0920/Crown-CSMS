from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "finance"
    verbose_name = "Finance"

    def ready(self):
        # Register cross-tenant/cross-payer money-integrity guards.
        from . import signals  # noqa: F401
