from django.apps import AppConfig


class SpiritualLifeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "spiritual_life"

    def ready(self):
        # Ensure the expanded Spiritual Life & Biblical Formation model module is
        # registered for runtime imports in deployments that still load the legacy
        # single-file spiritual_life.models module first.
        from spiritual_life import formation_models  # noqa: F401
