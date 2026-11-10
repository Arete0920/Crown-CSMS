"""Local demo route evidence must adapt as unmerged modules become available."""
from pathlib import Path
import importlib.util
import subprocess
import sys
from unittest.mock import patch

import pytest

from django.test import SimpleTestCase

from sandbox_demo.management.commands.five_module_demo_preflight import frontend_route_evidence, camp_entitlement_evidence


class FiveModuleRouteEvidenceTests(SimpleTestCase):
    def test_no_application_is_marked_available_without_verified_route_and_page(self):
        result = frontend_route_evidence("", "")
        self.assertEqual(len(result), 5)
        self.assertFalse(any(result.values()))

    def test_all_five_routed_modules_are_recognized_without_code_changes(self):
        paths = """
            FINANCIAL_AID PARENT_FINANCIAL_AID JIREH_SGO
            BEFORECARE_DIRECTOR AFTERCARE_DIRECTOR
            DIADEM_DIRECTOR SUMMER_CAMP_ROSTER
        """
        router = """
            PATHS.FINANCIAL_AID FinancialAidDashboard
            PATHS.PARENT_FINANCIAL_AID ParentFinancialAidPreparationPage
            PATHS.JIREH_SGO JirehSGODashboard
            PATHS.BEFORECARE_DIRECTOR CareSessionDirectorDashboard
            PATHS.AFTERCARE_DIRECTOR CareSessionDirectorDashboard
            PATHS.DIADEM_DIRECTOR DiademDirectorRosterPage
            PATHS.SUMMER_CAMP_ROSTER SummerCampRosterPage
        """
        self.assertTrue(all(frontend_route_evidence(paths, router).values()))

    def test_current_repository_route_evidence_is_dynamic(self):
        # This test must still pass after Jireh SGO and Diadem routes are added.
        root = Path(__file__).resolve().parents[3]
        routes = root / "frontend" / "dashboards" / "src" / "routes"
        result = frontend_route_evidence(
            (routes / "paths.js").read_text(encoding="utf-8"),
            (routes / "router.jsx").read_text(encoding="utf-8"),
        )
        self.assertEqual(set(result), {
            "Jireh Financial Aid", "Jireh SGO", "Extended Care",
            "Diadem Daycare", "Summer Camp",
        })
        self.assertTrue(result["Jireh Financial Aid"])
        self.assertTrue(result["Extended Care"])
        self.assertTrue(result["Summer Camp"])
        self.assertTrue(all(isinstance(ready, bool) for ready in result.values()))

def _load_heritage_launcher():
    path = Path(__file__).resolve().parents[3] / "scripts" / "demo" / "start_heritage_local.py"
    spec = importlib.util.spec_from_file_location("heritage_launcher_preflight", path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    return launcher


def test_launcher_runs_strict_audit_with_same_isolated_environment(tmp_path):
    launcher = _load_heritage_launcher()
    python = Path("isolated-demo") / "python.exe"
    env = {
        "CROWN_ENV": "local",
        "BUILD_SHA": "a" * 40,
        "DJANGO_DEBUG": "true",
        "DATABASE_URL": "sqlite:///fictional/heritage.sqlite3",
    }
    argv = ["start_heritage_local.py", "--prepare-only", "--five-module-preflight"]
    with patch.object(sys, "argv", argv), \
         patch.object(launcher, "STATE", tmp_path), \
         patch.object(launcher, "require_five_module_sources"), \
         patch.object(launcher, "source_sha", return_value="a" * 40), \
         patch.object(launcher, "available_ports"), \
         patch.object(launcher, "local_environment", return_value=env), \
         patch.object(launcher, "npm_command", return_value=["npm"]), \
         patch.object(launcher, "prepare", return_value=python), \
         patch.object(launcher, "seed_five_module_fixtures") as seeding, \
         patch.object(launcher, "run") as run_command:
        assert launcher.main() == 0
    seeding.assert_called_once_with(env, python)
    run_command.assert_called_once_with(
        [str(python), str(launcher.ROOT / "backend/manage.py"),
         "five_module_demo_preflight", "--strict"],
        env,
    )


def test_launcher_strict_audit_failure_returns_nonzero_without_starting_servers(tmp_path):
    launcher = _load_heritage_launcher()
    argv = ["start_heritage_local.py", "--prepare-only", "--five-module-preflight"]
    env = {"CROWN_ENV": "local", "BUILD_SHA": "a" * 40}
    python = Path("isolated-demo/python.exe")
    with patch.object(sys, "argv", argv), \
         patch.object(launcher, "STATE", tmp_path), \
         patch.object(launcher, "require_five_module_sources"), \
         patch.object(launcher, "source_sha", return_value="a" * 40), \
         patch.object(launcher, "available_ports"), \
         patch.object(launcher, "local_environment", return_value=env), \
         patch.object(launcher, "npm_command", return_value=["npm"]), \
         patch.object(launcher, "prepare", return_value=python), \
         patch.object(launcher, "seed_five_module_fixtures") as seeding, \
         patch.object(launcher, "run",
                      side_effect=subprocess.CalledProcessError(1, ["five_module_demo_preflight"])) as audit:
        assert launcher.main() == 1
    seeding.assert_called_once_with(env, python)
    audit.assert_called_once_with(
        [str(python), str(launcher.ROOT / "backend/manage.py"),
         "five_module_demo_preflight", "--strict"],
        env,
    )


def test_launcher_rejects_strict_audit_without_prepare_only():
    launcher = _load_heritage_launcher()
    with patch.object(sys, "argv", ["start_heritage_local.py", "--five-module-preflight"]):
        with pytest.raises(SystemExit) as exc:
            launcher.main()
    assert exc.value.code == 2


@pytest.mark.django_db
def test_camp_preflight_requires_real_school_entitlement():
    from datetime import timedelta

    from django.utils import timezone
    from core.models import School
    from subscriptions.models import SchoolModule

    school = School.objects.create(name="Fictional entitlement gate test")
    other = School.objects.create(name="Foreign fictional school")
    assert camp_entitlement_evidence(school.id) is False

    foreign_module = SchoolModule.objects.create(
        school=other, module_key="little_lambs", status="active",
        expiry_date=timezone.now() + timedelta(days=30),
    )
    assert camp_entitlement_evidence(school.id) is False
    assert camp_entitlement_evidence(other.id) is True

    own_module = SchoolModule.objects.create(
        school=school, module_key="little_lambs", status="active",
        expiry_date=timezone.now() + timedelta(days=30),
    )
    assert camp_entitlement_evidence(school.id) is True
    for status in ("inactive", "suspended", "expired"):
        own_module.status = status
        own_module.save(update_fields=["status"])
        assert camp_entitlement_evidence(school.id) is False
    own_module.status = "active"
    own_module.expiry_date = timezone.now() - timedelta(days=1)
    own_module.save(update_fields=["status", "expiry_date"])
    assert camp_entitlement_evidence(school.id) is False

    foreign_module.status = "inactive"
    foreign_module.save(update_fields=["status"])
    assert camp_entitlement_evidence(other.id) is False


@pytest.mark.django_db
def test_local_preflight_does_not_accept_legacy_financial_aid_as_canonical_jireh(monkeypatch):
    from datetime import date
    from io import StringIO
    from uuid import UUID, uuid4

    from django.core.management import call_command
    from core.models import AcademicYear, Family, School, Student
    from financial_aid.models import FinancialAidApplication, AidAward as LegacyAidAward
    from aid.models import AidApplication, AidAward as CanonicalAidAward
    from sandbox_demo.catalog import SANDBOX_SCHOOLS
    from sandbox_demo.management.commands import five_module_demo_preflight as module

    school = School.objects.create(
        pk=UUID(SANDBOX_SCHOOLS["heritage-core"].id),
        name="Heritage Christian Academy", timezone="America/New_York",
    )
    legacy = FinancialAidApplication.objects.create(
        school_id=school.id, household_id=uuid4(), academic_year="2026-27",
    )
    LegacyAidAward.objects.create(
        school_id=school.id, application=legacy, bucket="need", amount=1200,
    )
    monkeypatch.setattr(module, "_require_isolated_local_database", lambda: None)
    output = StringIO()
    call_command("five_module_demo_preflight", stdout=output)
    assert "FAIL Jireh canonical applications:" in output.getvalue()
    assert "FAIL Jireh canonical offered awards:" in output.getvalue()

    year = AcademicYear.objects.create(
        school=school, name="2026-2027",
        start_date=date(2026, 8, 15), end_date=date(2027, 6, 5),
    )
    family = Family.objects.create(school=school, family_name="Fictional Jireh household")
    student = Student.objects.create(
        school=school, family=family, student_number="FICT-JIREH-001",
        first_name="Fictional", last_name="Learner", dob=date(2014, 2, 2),
    )
    application = AidApplication.objects.create(
        school=school, academic_year=year, family=family, status="SUBMITTED",
    )
    CanonicalAidAward.objects.create(
        school=school, academic_year=year, student=student,
        aid_application=application, awarded_cents=120000,
        decision_status="OFFERED",
    )
    output = StringIO()
    call_command("five_module_demo_preflight", stdout=output)
    assert "PASS Jireh canonical applications:" in output.getvalue()
    assert "PASS Jireh canonical offered awards:" in output.getvalue()


@pytest.mark.django_db
def test_local_preflight_sgo_requires_active_grantor_and_member(monkeypatch):
    from io import StringIO
    from uuid import UUID, uuid4

    from django.core.management import call_command
    from core.models import School, UserAccount
    from jireh_sgo.models import (
        SGOApplication, SGOMembership, SGOOrganization, SGOProgram,
    )
    from sandbox_demo.catalog import SANDBOX_SCHOOLS
    from sandbox_demo.management.commands import five_module_demo_preflight as module

    school = School.objects.create(
        pk=UUID(SANDBOX_SCHOOLS["heritage-core"].id),
        name="Heritage Christian Academy",
        timezone="America/New_York",
    )
    org = SGOOrganization.objects.create(
        legal_name="Fictional independent grantor", state_of_domicile="DE",
        active=False,
    )
    program = SGOProgram.objects.create(
        organization=org, name="Fictional scholarship pilot",
        code="fictional-scholarship", calendar_year=2027,
        funding_source="PRIVATE", eligibility_rule_version="POLICY_2027_V1",
    )
    SGOApplication.objects.create(
        program=program, school_key=school.id, student_key=uuid4(),
    )
    monkeypatch.setattr(module, "_require_isolated_local_database", lambda: None)

    def output():
        stream = StringIO()
        call_command("five_module_demo_preflight", stdout=stream)
        return stream.getvalue()

    assert "FAIL Jireh SGO active-grantor noncash applications:" in output()
    org.active = True
    org.save(update_fields=["active"])
    assert "FAIL Jireh SGO active-grantor noncash applications:" in output()

    reviewer = UserAccount.objects.create_user(
        username="fictional-grantor-reviewer", password="synthetic",
        is_active=True,
    )
    membership = SGOMembership.objects.create(
        organization=org, user=reviewer,
        role=SGOMembership.VIEWER, active=True,
    )
    assert "PASS Jireh SGO active-grantor noncash applications:" in output()
    membership.active = False
    membership.save(update_fields=["active"])
    assert "FAIL Jireh SGO active-grantor noncash applications:" in output()
