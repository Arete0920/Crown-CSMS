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
def test_existing_dev_aid_only_preflight_and_apply_do_not_stage_other_modules(local_runtime):
    """Only institutional Aid policy and the authorized officer; no SGO or care."""
    from aid.models import AidApplication, AidPolicy
    from aftercare.models import DaycareChild
    from core.models import Family, Student, UserRole
    from jireh_sgo.models import SGOFamilyGrant, SGOOrganization, SGOProgram
    from sandbox_demo.universal_demo import require_local_presenter
    call_command("seed_permissions", stdout=StringIO())
    with patch(COMMAND + ".require_hosted_presenter", side_effect=lambda sha: require_local_presenter()):
        preflight = StringIO()
        call_command("provision_universal_presenter", expected_sha=SHA,
                     financial_aid_only=True, stdout=preflight)
        assert not School.objects.exists()
        assert '"scope": "FINANCIAL_AID_ONLY"' in preflight.getvalue()
        result = StringIO()
        call_command("provision_universal_presenter", expected_sha=SHA, apply=True,
                     confirm_school_id=str(UNIVERSAL_SCHOOL_ID),
                     financial_aid_only=True, stdout=result)
    assert '"scope": "FINANCIAL_AID_ONLY"' in result.getvalue()
    assert School.objects.count() == AidPolicy.objects.count() == 1
    assert Student.objects.filter(
        school_id=UNIVERSAL_SCHOOL_ID, family__family_name="Reed Family"
    ).count() == 2
    assert Family.objects.filter(school_id=UNIVERSAL_SCHOOL_ID, family_name="Reed Family").count() == 1
    assert UserRole.objects.filter(school_id=UNIVERSAL_SCHOOL_ID, role_code="AID_DIRECTOR").count() == 1
    assert not AidApplication.objects.exists()  # No invented submission or award.
    assert not DaycareChild.objects.exists()
    assert not SGOOrganization.objects.exists()
    assert not SGOProgram.objects.exists()
    assert not SGOFamilyGrant.objects.exists()




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

@pytest.mark.django_db
def test_owner_opt_in_stages_audited_non_cash_reed_case_atomically(local_runtime):
    """No Azure access: only the isolated fictional local test runtime."""
    from aid.models import AidApplication, AidAward, AidAuditEvent, AidBudgetTracker
    from core.models import School, Student
    from ledger.models import Credit, Payment
    from aftercare.models import DaycareChild
    from jireh_sgo.models import SGOFamilyGrant
    from sandbox_demo.universal_demo import require_local_presenter
    from sandbox_demo.website_presenter import website_financial_aid_ready

    call_command("seed_permissions", stdout=StringIO())
    with patch(COMMAND + ".require_hosted_presenter",
               side_effect=lambda sha: require_local_presenter()):
        result = StringIO()
        call_command(
            "provision_universal_presenter", expected_sha=SHA,
            apply=True, financial_aid_only=True, stage_fictional_aid_case=True,
            confirm_school_id=str(UNIVERSAL_SCHOOL_ID), stdout=result,
        )
    school = School.objects.get(pk=UNIVERSAL_SCHOOL_ID)
    assert '"case_ready": true' in result.getvalue()
    assert website_financial_aid_ready(school)
    application = AidApplication.objects.get(school=school)
    assert application.status == AidApplication.STATUS_SUBMITTED
    assert application.submitted_at and application.financial_profile_id
    assert Student.objects.filter(school=school, family=application.family).count() == 2
    award = AidAward.objects.get(school=school, aid_application=application)
    assert award.decision_status == AidAward.DECISION_ACCEPTED
    assert award.awarded_cents == 25_000 and award.ledger_entry_id
    assert award.decided_by_id is None
    assert AidBudgetTracker.objects.get(
        school=school, academic_year=application.academic_year,
        bucket=AidAward.TYPE_NEED,
    ).awarded_cents == 25_000
    credit = Credit.objects.get(
        school_id=school.pk, source=Credit.SOURCE_FINANCIAL_AID,
        reference=f"aid_award:{award.pk}",
    )
    assert str(credit.amount) == "250.00"
    assert not credit.is_void and credit.account.school_id == school.pk
    assert not Payment.objects.filter(school_id=school.pk).exists()
    assert not DaycareChild.objects.exists()
    assert not SGOFamilyGrant.objects.exists()
    assert AidAuditEvent.objects.filter(
        school=school, entity_id=str(award.pk), action="AWARD_APPROVED",
        actor_user__isnull=True,
    ).count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("flags", [
    {"financial_aid_only": True},
    {"apply": True},
    {"apply": True, "financial_aid_only": True, "enable_password_login": True},
    {"apply": True, "financial_aid_only": True, "archive_classroom": True},
])
def test_owner_synthetic_case_requires_explicit_guarded_initial_apply(
    local_runtime, flags,
):
    from sandbox_demo.universal_demo import require_local_presenter
    with patch(COMMAND + ".require_hosted_presenter",
               side_effect=lambda sha: require_local_presenter()):
        with pytest.raises(CommandError, match="Synthetic case staging requires"):
            call_command(
                "provision_universal_presenter", expected_sha=SHA,
                stage_fictional_aid_case=True, **flags, stdout=StringIO(),
            )
    assert not School.objects.exists()


@pytest.mark.django_db
def test_owner_synthetic_case_failure_rolls_back_initial_provision(local_runtime):
    from sandbox_demo.universal_demo import require_local_presenter
    call_command("seed_permissions", stdout=StringIO())
    with patch(COMMAND + ".require_hosted_presenter",
               side_effect=lambda sha: require_local_presenter()), patch(
        COMMAND + ".stage_owner_fictional_aid_case",
        side_effect=CommandError("synthetic case rollback probe"),
    ):
        with pytest.raises(CommandError, match="rollback probe"):
            call_command(
                "provision_universal_presenter", expected_sha=SHA,
                apply=True, financial_aid_only=True,
                stage_fictional_aid_case=True,
                confirm_school_id=str(UNIVERSAL_SCHOOL_ID),
                stdout=StringIO(),
            )
    assert not School.objects.exists() and not UserAccount.objects.exists()
