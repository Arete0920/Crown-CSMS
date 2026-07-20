from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/release/production_surface_inventory.py"
SPEC = importlib.util.spec_from_file_location("production_surface_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

Surface = MODULE.Surface


def write(root: Path, relative: str, content: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fixture_repo(root: Path) -> None:
    write(
        root,
        "frontend/dashboards/src/routes/paths.js",
        """export const PATHS = {
  HOME: '/',
  BILLING: '/billing',
  PARENT_BILLING_PAY: '/parent/billing/pay',
  SYSTEM_STATUS: '/system-status',
};
""",
    )
    write(
        root,
        "frontend/dashboards/src/config/dashboardRegistry.js",
        """import { PATHS } from '../routes/paths';
export const DASHBOARD_REGISTRY = [
  createDashboard({ key: 'billing', label: 'Billing', path: PATHS.BILLING }),
  createDashboard({ key: 'literal', label: 'Literal', path: '/literal-dashboard' }),
];
""",
    )
    write(
        root,
        "frontend/dashboards/src/routes/wizard-manifest.js",
        """export const WIZARD_MANIFEST = [
  { slug: 'billing-wizard', title: 'Billing Setup', path: '/billing-setup' },
  { slug: 'staff-wizard', title: 'Staff Setup', path: '/staff-setup' },
];
""",
    )
    write(
        root,
        "frontend/dashboards/src/pages/BillingWizard.jsx",
        """const BILLING_STEPS = [
  { id: 'fees', title: 'Fees' },
  { id: 'review', label: 'Review' },
];
export default function BillingWizard() { return null; }
""",
    )
    write(
        root,
        "backend/billing/apps.py",
        """from django.apps import AppConfig
class BillingConfig(AppConfig):
    name = 'billing'
""",
    )
    write(
        root,
        "backend/billing/tasks.py",
        """from celery import shared_task
@shared_task
def reconcile_invoices():
    return None

def helper_task():
    return None
""",
    )


def test_collects_actual_registry_shapes(tmp_path: Path) -> None:
    fixture_repo(tmp_path)
    paths, routes = MODULE.parse_paths(tmp_path)
    dashboards = MODULE.parse_dashboards(tmp_path, paths)
    wizards = MODULE.parse_wizards(tmp_path)
    steps = MODULE.parse_wizard_steps(tmp_path)
    modules = MODULE.parse_backend_modules(tmp_path)
    tasks = MODULE.parse_tasks(tmp_path)

    assert paths["BILLING"] == "/billing"
    assert {row.surface_id for row in dashboards} == {"dashboard:billing", "dashboard:literal"}
    assert {row.path for row in dashboards} == {"/billing", "/literal-dashboard"}
    assert {row.surface_id for row in wizards} == {"wizard:billing-wizard", "wizard:staff-wizard"}
    assert {row.surface_id for row in steps} == {
        "wizard_step:billingwizard:fees",
        "wizard_step:billingwizard:review",
    }
    assert [row.surface_id for row in modules] == ["module:backend:billing"]
    assert {row.surface_id for row in tasks} == {
        "task:billing:helper-task",
        "task:billing:reconcile-invoices",
    }


def test_classification_preserves_accounting_and_excludes_processing() -> None:
    accounting = MODULE.classify(
        Surface("frontend_route:billing", "frontend_route", "BILLING", "/billing", "paths.js", 1)
    )
    processing = MODULE.classify(
        Surface(
            "frontend_route:parent-billing-pay",
            "frontend_route",
            "PARENT_BILLING_PAY",
            "/parent/billing/pay",
            "paths.js",
            2,
        )
    )
    assert accounting.classification == "CRAWLER"
    assert processing.classification == "EXCLUDED_PAYMENT_PROCESSING"


def test_unknown_domain_is_genuinely_unmapped() -> None:
    row = MODULE.classify(Surface("new:surface", "new_domain", "New", "/new", "new.py", 1))
    assert row.classification == "UNMAPPED"
    assert MODULE.validate([row], require_domains=False) == []


def test_unresolved_dashboard_path_stays_unmapped(tmp_path: Path) -> None:
    fixture_repo(tmp_path)
    source = tmp_path / "frontend/dashboards/src/config/dashboardRegistry.js"
    source.write_text(
        "export const DASHBOARD_REGISTRY = [createDashboard({ key: 'broken', label: 'Broken', path: PATHS.MISSING })];\n",
        encoding="utf-8",
    )
    paths, _ = MODULE.parse_paths(tmp_path)
    row = MODULE.classify(MODULE.parse_dashboards(tmp_path, paths)[0])
    assert row.path == ""
    assert row.classification == "UNMAPPED"


def test_duplicate_ids_fail() -> None:
    row = Surface("api:one", "api", "one", "/api/one/", "urls.py", 1, "API_CONTRACT")
    errors = MODULE.validate([row, replace(row, source_line=2)], require_domains=False)
    assert errors == ["duplicate surface_id values: api:one"]


def test_required_domains_fail_closed() -> None:
    errors = MODULE.validate(
        [Surface("api:one", "api", "one", "/api/one/", "urls.py", 1, "API_CONTRACT")]
    )
    assert errors and errors[0].startswith("missing required domains:")


def test_digest_is_order_independent() -> None:
    first = Surface("api:a", "api", "a", "/a/", "a.py", 1, "API_CONTRACT")
    second = Surface("api:b", "api", "b", "/b/", "b.py", 1, "API_CONTRACT")
    assert MODULE.digest_rows([first, second]) == MODULE.digest_rows([second, first])


class FakeLeaf:
    def __init__(self, route: str, name: str) -> None:
        self.pattern = route
        self.name = name
        self.callback = lambda: None


class FakeResolver:
    def __init__(self, route: str, children: list[object]) -> None:
        self.pattern = route
        self.url_patterns = children


def test_nested_django_routes_are_composed() -> None:
    patterns = [FakeResolver("api/v1/", [FakeResolver("billing/", [FakeLeaf("invoices/", "invoice-list")])])]
    rows = MODULE.flatten_urlpatterns(patterns)
    assert [(route, name) for route, name, _ in rows] == [("api/v1/billing/invoices/", "invoice-list")]


def test_json_payload_contains_only_supported_classifications(tmp_path: Path) -> None:
    fixture_repo(tmp_path)
    paths, route_rows = MODULE.parse_paths(tmp_path)
    rows = route_rows + MODULE.parse_dashboards(tmp_path, paths) + MODULE.parse_wizards(tmp_path)
    rows += MODULE.parse_wizard_steps(tmp_path) + MODULE.parse_backend_modules(tmp_path) + MODULE.parse_tasks(tmp_path)
    classified = [MODULE.classify(row) for row in rows]
    payload = MODULE.row_payload(classified)
    encoded = json.dumps(payload, sort_keys=True)
    assert "UNMAPPED" not in encoded
    assert all(row["classification"] in MODULE.SUPPORTED_CLASSIFICATIONS for row in payload)
