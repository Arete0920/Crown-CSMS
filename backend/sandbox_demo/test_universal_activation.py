"""Source guard/atomicity proof only; no Azure connection or hosted certification."""
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from core.models import School, UserAccount
from sandbox_demo.test_universal_access import operator_secrets, login
from sandbox_demo.test_universal_presenter import local_runtime
from sandbox_demo.universal_identity import UNIVERSAL_SCHOOL_ID
from sandbox_demo.universal_runtime import require_hosted_presenter

SHA = "a" * 40
COMMAND = "sandbox_demo.management.commands.provision_universal_presenter"


@pytest.fixture
def hosted_guard(settings, monkeypatch):
    settings.CROWN_ENV = "dev"
    settings.DJANGO_ENV = "development"
    settings.DEBUG = False
    settings.BUILD_SHA = SHA
    settings.CROWN_DEMO_MODE = False
    settings.CROWN_SANDBOX_ALLOW_OPEN_SESSION = False
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = True
    settings.CROWN_UNIVERSAL_PRESENTER_ENABLED = True
    settings.CROWN_UNIVERSAL_PRESENTER_APPROVED_SHA = SHA
    settings.CROWN_UNIVERSAL_PRESENTER_APPROVED_DB_NAME = "synthetic_test_only"
    for key in ("ENVIRONMENT", "APP_ENV", "CROWN_ENV", "DJANGO_ENV", "AZURE_ENVIRONMENT", "CROWN_SANDBOX_OUTBOUND_DISABLED"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-dev.azurewebsites.net")
    conn = SimpleNamespace(vendor="postgresql", settings_dict={"NAME": "synthetic_test_only", "HOST": "crown-pg-dev.postgres.database.azure.com", "PORT": "5432"})
    with patch("sandbox_demo.universal_runtime.connection", conn), patch(
        "sandbox_demo.management.commands.provision_hosted_buyer_workspace.connection", conn):
        yield conn


def test_exact_owner_enabled_existing_dev_guard_is_source_only(hosted_guard):
    require_hosted_presenter(SHA)


@pytest.mark.parametrize("setting,value", [
    ("CROWN_UNIVERSAL_PRESENTER_ENABLED", False), ("CROWN_UNIVERSAL_PRESENTER_APPROVED_SHA", "b" * 40),
    ("CROWN_UNIVERSAL_PRESENTER_APPROVED_DB_NAME", ""),
    ("BUILD_SHA", "b" * 40), ("CROWN_ENV", "production"), ("DEBUG", True),
    ("CROWN_SANDBOX_ALLOW_OPEN_SESSION", True), ("CROWN_DEMO_MODE", True),
    ("CROWN_SANDBOX_OUTBOUND_DISABLED", False), ("APP_ENV", "staging"),
])
def test_unsafe_activation_settings_deny_before_queries(hosted_guard, settings, setting, value):
    setattr(settings, setting, value)
    with pytest.raises(CommandError):
        require_hosted_presenter(SHA)


@pytest.mark.parametrize("mutation", ["vendor", "host", "alternate_azure_host", "database", "wrong_database", "webhost"])
def test_unsafe_database_or_host_is_denied(hosted_guard, monkeypatch, mutation):
    if mutation == "vendor":
        hosted_guard.vendor = "sqlite"
    elif mutation == "host":
        hosted_guard.settings_dict["HOST"] = "customer-db.example.invalid"
    elif mutation == "alternate_azure_host":
        hosted_guard.settings_dict["HOST"] = "other.postgres.database.azure.com"
    elif mutation == "database":
        hosted_guard.settings_dict["NAME"] = ""
    elif mutation == "wrong_database":
        hosted_guard.settings_dict["NAME"] = "wrong_dev_database"
    else:
        monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-prod.azurewebsites.net")
    with pytest.raises(CommandError):
        require_hosted_presenter(SHA)


@pytest.mark.django_db
def test_activation_preflight_and_atomic_apply_on_disposable_sqlite_only(local_runtime, operator_secrets):
    from sandbox_demo.universal_demo import require_local_presenter
    from aid.models import AidPolicy
    from aftercare.models import DaycareChild
    from sandbox_demo.models import SandboxBuyerWorkspace
    call_command("seed_permissions", stdout=StringIO())
    with patch(COMMAND + ".require_hosted_presenter", side_effect=lambda sha: require_local_presenter()):
        call_command("provision_universal_presenter", expected_sha=SHA, stdout=StringIO())
        assert not School.objects.exists()
        call_command("provision_universal_presenter", expected_sha=SHA, apply=True,
            confirm_school_id=str(UNIVERSAL_SCHOOL_ID), enable_password_login=True, stdout=StringIO())
        assert School.objects.count() == 1 and AidPolicy.objects.count() == 1 and DaycareChild.objects.count() == 1
        assert not SandboxBuyerWorkspace.objects.exists()
        before = dict(UserAccount.objects.values_list("pk", "password"))
        with pytest.raises(CommandError, match="already exists"):
            call_command("provision_universal_presenter", expected_sha=SHA, apply=True,
                confirm_school_id=str(UNIVERSAL_SCHOOL_ID), stdout=StringIO())
        assert before == dict(UserAccount.objects.values_list("pk", "password"))
        login("parent", operator_secrets)


@pytest.mark.django_db
def test_module_failure_rolls_back_whole_activation(local_runtime, operator_secrets):
    from sandbox_demo.universal_demo import require_local_presenter
    from subscriptions.models import Plan
    call_command("seed_permissions", stdout=StringIO())
    with patch(COMMAND + ".require_hosted_presenter", side_effect=lambda sha: require_local_presenter()), patch(
        COMMAND + ".prepare_presenter_jireh", side_effect=CommandError("synthetic rollback probe")):
        with pytest.raises(CommandError, match="rollback probe"):
            call_command("provision_universal_presenter", expected_sha=SHA, apply=True,
                confirm_school_id=str(UNIVERSAL_SCHOOL_ID), stdout=StringIO())
    assert not School.objects.exists() and not UserAccount.objects.exists() and not Plan.objects.exists()


@pytest.mark.django_db
def test_local_commands_do_not_become_hosted_provisioners(local_runtime, settings, django_assert_num_queries):
    settings.CROWN_ENV = "dev"
    settings.CROWN_UNIVERSAL_PRESENTER_ENABLED = True
    for name in ("prepare_universal_presenter", "prepare_universal_care", "prepare_universal_jireh"):
        with django_assert_num_queries(0), pytest.raises(CommandError):
            call_command(name, apply=True, stdout=StringIO())
