from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "academics"

    def ready(self) -> None:
        from . import submission_defaults  # noqa: F401
        from . import tenant_guards  # noqa: F401
