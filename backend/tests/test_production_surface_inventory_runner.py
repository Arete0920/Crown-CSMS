from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[2] / "scripts/release/production_surface_inventory_runner.py"
SPEC = importlib.util.spec_from_file_location("production_surface_inventory_runner", RUNNER)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_dashboard_function_declaration_is_not_inventory(tmp_path: Path) -> None:
    write(
        tmp_path,
        "frontend/dashboards/src/config/dashboardRegistry.js",
        """function createDashboard({ key, label, path }) { return { key, label, path }; }
export const DASHBOARD_REGISTRY = [
  createDashboard({ key: 'billing', label: 'Billing', path: PATHS.BILLING }),
];
""",
    )
    rows = MODULE.dashboards(tmp_path, {"BILLING": "/billing"})
    assert [row.surface_id for row in rows] == ["dashboard:billing"]
    assert rows[0].path == "/billing"


def test_step_files_are_discovered_outside_wizard_named_files(tmp_path: Path) -> None:
    write(
        tmp_path,
        "frontend/dashboards/src/pages/onboarding/Step1ChooseMode.jsx",
        "export default function Step1ChooseMode() { return null; }\n",
    )
    write(
        tmp_path,
        "frontend/dashboards/src/pages/billing_wizard/Step3Fees.jsx",
        "export default function Step3Fees() { return null; }\n",
    )
    assert {row.surface_id for row in MODULE.wizard_steps(tmp_path)} == {
        "wizard_step:onboarding:step1choosemode",
        "wizard_step:billing-wizard:step3fees",
    }


def test_only_decorated_tasks_are_inventory(tmp_path: Path) -> None:
    write(
        tmp_path,
        "backend/billing/tasks.py",
        """from celery import shared_task
@shared_task
def reconcile_invoices():
    return None

def helper_task():
    return None
""",
    )
    rows = MODULE.tasks(tmp_path)
    assert [row.surface_id for row in rows] == ["task:billing:reconcile-invoices"]
