import os

def pytest_configure(config):
    # This runs early in pytest startup.
    print("\n=== PYTEST DJANGO DIAGNOSTICS (EARLY) ===")
    print("DJANGO_SETTINGS_MODULE env:", os.environ.get("DJANGO_SETTINGS_MODULE"))
    try:
        import django
        from django.conf import settings
        django.setup()
        print("settings module:", getattr(settings, "SETTINGS_MODULE", None))
        print("INSTALLED_APPS has core?:", any(
            a == "core" or a.endswith(".core") or a.endswith("core.apps.CoreConfig")
            for a in settings.INSTALLED_APPS
        ))
        mm = getattr(settings, "MIGRATION_MODULES", None)
        print("MIGRATION_MODULES:", mm)
        if isinstance(mm, dict):
            print("MIGRATION_MODULES['core']:", mm.get("core"))
            print("MIGRATION_MODULES['finance']:", mm.get("finance"))
    except Exception as e:
        print("django.setup() failed:", repr(e))

    # Prove what Python imports for core and its migrations package
    try:
        import core
        print("core.__file__:", getattr(core, "__file__", None))
        import core.migrations
        print("core.migrations.__file__:", getattr(core.migrations, "__file__", None))
    except Exception as e:
        print("import core/core.migrations failed:", repr(e))

    print("=== END DIAGNOSTICS ===\n")

    # Ensure demo write-block middleware does not interfere with tests.
    # Individual tests opt in via @override_settings(CROWN_DEMO_MODE=True).
    settings.CROWN_DEMO_MODE = False

    # Disable tenant header enforcement globally in tests.
    # Individual tests opt in via @override_settings(TENANT_HEADER_REQUIRED=True).
    settings.TENANT_HEADER_REQUIRED = False
