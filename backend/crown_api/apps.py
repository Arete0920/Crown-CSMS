from django.apps import AppConfig


class CrownApiConfig(AppConfig):
    name = "crown_api"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        # Schema discovery imports REST framework settings. Register only after
        # Django has finished loading settings, so API defaults are not cached
        # before CROWN's authentication/permission configuration exists.
        from . import spectacular_extensions  # noqa: F401
