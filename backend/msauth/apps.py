from django.apps import AppConfig


class MsauthConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "msauth"
    label = "msauth"
    verbose_name = "Microsoft SSO Auth"
