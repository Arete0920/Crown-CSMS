import importlib.util
import os
import sys
import types
from pathlib import Path


# Keep repository and backend modules importable when pytest is invoked from
# either the repository root or the backend directory in local and CI runs.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPOSITORY_ROOT / "backend"
REPOSITORY_TOOLS_ROOT = REPOSITORY_ROOT / "tools"
BACKEND_TOOLS_ROOT = BACKEND_ROOT / "tools"
for path in (REPOSITORY_ROOT, BACKEND_ROOT):
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

# Some installed dependencies expose a top-level ``tools`` module before test
# collection. Pin ``tools`` to both repository tool roots, preserving imports
# for release validators and backend import-management modules.
tools_package = types.ModuleType("tools")
tools_package.__path__ = [str(REPOSITORY_TOOLS_ROOT), str(BACKEND_TOOLS_ROOT)]
tools_package.__package__ = "tools"
sys.modules["tools"] = tools_package

for module_name in (
    "validate_recovery_closure_evidence",
    "validate_recovery_evidence",
    "validate_secret_store_evidence",
):
    qualified_name = f"tools.{module_name}"
    module_path = REPOSITORY_TOOLS_ROOT / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load repository validator: {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified_name] = module
    spec.loader.exec_module(module)


def pytest_configure(config):
    # Conventions for API tenant context in tests:
    # see backend/tests/TEST_CONVENTIONS.md

    # This runs early in pytest startup.
    print("\n=== PYTEST DJANGO DIAGNOSTICS (EARLY) ===")
    print("DJANGO_SETTINGS_MODULE env:", os.environ.get("DJANGO_SETTINGS_MODULE"))
    print("repository root on sys.path:", str(REPOSITORY_ROOT) in sys.path)
    print("backend root on sys.path:", str(BACKEND_ROOT) in sys.path)
    print("tools package path:", list(getattr(sys.modules.get("tools"), "__path__", [])))
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
