from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"

    def ready(self):
        from .tenant_m2m_guard import install_tenant_m2m_guards

        install_tenant_m2m_guards()
