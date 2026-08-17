from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "academics"

    def ready(self) -> None:
        from . import lesson_execution_models  # noqa: F401
        from . import lesson_execution_signals  # noqa: F401
        from . import submission_defaults  # noqa: F401
        from . import tenant_guards  # noqa: F401
        from .bulk_writer_guards import install_academics_bulk_writer_guards

        install_academics_bulk_writer_guards()
