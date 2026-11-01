"""Local demo route evidence must adapt as unmerged modules become available."""
from pathlib import Path
import importlib.util
import subprocess
import sys
from unittest.mock import patch

import pytest

from django.test import SimpleTestCase

from sandbox_demo.management.commands.five_module_demo_preflight import frontend_route_evidence


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


def test_launcher_runs_strict_audit_with_same_isolated_environment():
    launcher = _load_heritage_launcher()
    python = Path("isolated-demo") / "python.exe"
    env = {
        "CROWN_ENV": "local",
        "DJANGO_DEBUG": "true",
        "DATABASE_URL": "sqlite:///fictional/heritage.sqlite3",
    }
    argv = ["start_heritage_local.py", "--prepare-only", "--five-module-preflight"]
    with patch.object(sys, "argv", argv), \
         patch.object(launcher, "available_ports"), \
         patch.object(launcher, "local_environment", return_value=env), \
         patch.object(launcher, "npm_command", return_value=["npm"]), \
         patch.object(launcher, "prepare", return_value=python), \
         patch.object(launcher, "run") as run_command:
        assert launcher.main() == 0
    run_command.assert_called_once_with(
        [str(python), str(launcher.ROOT / "backend/manage.py"),
         "five_module_demo_preflight", "--strict"],
        env,
    )


def test_launcher_strict_audit_failure_returns_nonzero_without_starting_servers():
    launcher = _load_heritage_launcher()
    argv = ["start_heritage_local.py", "--prepare-only", "--five-module-preflight"]
    with patch.object(sys, "argv", argv), \
         patch.object(launcher, "available_ports"), \
         patch.object(launcher, "local_environment", return_value={"CROWN_ENV": "local"}), \
         patch.object(launcher, "npm_command", return_value=["npm"]), \
         patch.object(launcher, "prepare", return_value=Path("isolated-demo/python.exe")), \
         patch.object(launcher, "run",
                      side_effect=subprocess.CalledProcessError(1, ["five_module_demo_preflight"])):
        assert launcher.main() == 1


def test_launcher_rejects_strict_audit_without_prepare_only():
    launcher = _load_heritage_launcher()
    with patch.object(sys, "argv", ["start_heritage_local.py", "--five-module-preflight"]):
        with pytest.raises(SystemExit) as exc:
            launcher.main()
    assert exc.value.code == 2
