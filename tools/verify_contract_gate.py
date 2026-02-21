# tools/verify_contract_gate.py
# Phase 5 Contract Gate (API surface integrity)
# Enforces:
# 1) Critical endpoints resolve (path exists in URL router)
# 2) Allowed HTTP methods match contract (no silent method stripping)
#
# No live server, no DB connection, no migrations required.
# Pure Django URL resolution — runs in < 5s.

import os
import sys
import django
from pathlib import Path

# ── Bootstrap ────────────────────────────────────────────────────────────────
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root / "backend"))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
os.environ.setdefault("SECRET_KEY", "ci-not-secret")
os.environ.setdefault("DEBUG", "0")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("DATABASE_URL", "sqlite:///./ci.sqlite3")

django.setup()

from django.urls import resolve, Resolver404  # noqa: E402

# ── Helpers ───────────────────────────────────────────────────────────────────
_DUMMY_UUID = "00000000-0000-0000-0000-000000000001"
_DUMMY_STR  = "ci-dummy-id"


def _allowed_methods(func) -> set[str]:
    """Return the set of uppercase HTTP methods the view accepts."""
    cls = getattr(func, "cls", None) or getattr(func, "view_class", None)
    if cls is None:
        # Wrapped CBV or plain function — skip method check
        return set()
    names = getattr(cls, "http_method_names", [])
    return {m.upper() for m in names}


def check(label: str, path: str, methods: list[str]) -> list[str]:
    """Resolve *path* and verify *methods* are present. Returns error strings."""
    errors = []
    try:
        match = resolve(path)
    except Resolver404:
        errors.append(f"MISSING ROUTE  [{label}]  {path}")
        return errors

    if methods:
        allowed = _allowed_methods(match.func)
        if allowed:  # only assert when we can introspect (skip opaque views)
            missing = {m.upper() for m in methods} - allowed
            if missing:
                errors.append(
                    f"WRONG METHODS  [{label}]  {path}  "
                    f"expected={sorted(methods)}  allowed={sorted(allowed)}"
                )
    return errors


# ── Contract Table ────────────────────────────────────────────────────────────
# (label, path, [required_methods])
# Use _DUMMY_UUID / _DUMMY_STR for parameterised segments.
CONTRACT = [
    # ── Health & system ──────────────────────────────────────────────────────
    ("health",                "/health/",                          ["GET"]),
    ("api-health",            "/api/health/",                      ["GET"]),
    ("system-health",         "/api/system/health/",               ["GET"]),
    ("system-whoami",         "/api/system/whoami/",               ["GET"]),
    ("version",               "/api/v1/version/",                  ["GET"]),

    # ── Auth ─────────────────────────────────────────────────────────────────
    ("auth-login",            "/api/auth/login/",                  ["POST"]),
    ("auth-refresh",          "/api/auth/refresh/",                ["POST"]),
    ("auth-me",               "/api/auth/me/",                     ["GET"]),
    ("dev-token",             "/api/dev/token/",                   ["POST"]),

    # ── Ops / RBAC / audit ───────────────────────────────────────────────────
    ("ops-summary",           "/api/ops/summary/",                 ["GET"]),
    ("ops-alerts",            "/api/ops/alerts/",                  ["GET"]),
    ("rbac-finance-proof",    "/api/system/rbac/finance-proof/",   ["GET"]),
    ("audit-recent",          "/api/system/audit/recent/",         ["GET"]),

    # ── Director (legacy unified) ─────────────────────────────────────────────
    ("director-actions",      "/api/director/actions/",            ["POST"]),
    ("director-dashboard",    "/api/director/dashboard/",          ["GET"]),
    ("director-priority",     "/api/director/priority/",           ["GET"]),
    ("director-timeline",     "/api/director/timeline/",           ["GET"]),
    ("director-aid-summary",  "/api/director/aid/summary/",        ["GET"]),
    ("director-fin-summary",  "/api/director/finance/summary/",    ["GET"]),

    # ── Households ───────────────────────────────────────────────────────────
    ("households-list",       "/api/households/",                  ["GET"]),
    ("household-detail",      f"/api/households/{_DUMMY_UUID}/",   ["GET"]),

    # ── Students ─────────────────────────────────────────────────────────────
    ("students-list",         "/api/students/",                    ["GET"]),
    ("student-detail",        f"/api/students/{_DUMMY_UUID}/",     ["GET"]),
    ("student-grades",        f"/api/students/{_DUMMY_UUID}/grades/",     ["GET"]),
    ("student-attendance",    f"/api/students/{_DUMMY_UUID}/attendance/", ["GET"]),
    ("student-schedule",      f"/api/students/{_DUMMY_UUID}/schedule/",   ["GET"]),

    # ── Applications / Admissions ─────────────────────────────────────────────
    ("applications-list",     "/api/applications/",                        ["GET", "POST"]),
    ("application-detail",    f"/api/applications/{_DUMMY_STR}/",          ["GET"]),
    ("application-submit",    f"/api/applications/{_DUMMY_STR}/submit/",   ["POST"]),
    ("application-decision",  f"/api/applications/{_DUMMY_STR}/decision/", ["POST"]),
    ("applicants",            "/api/applicants/",                          ["GET"]),

    # ── Ledger ───────────────────────────────────────────────────────────────
    ("ledger-ensure-account", "/api/ledger/accounts/ensure/",                          ["POST"]),
    ("ledger-account-detail", f"/api/ledger/accounts/{_DUMMY_STR}/",                   ["GET"]),
    ("ledger-statement",      f"/api/ledger/accounts/{_DUMMY_STR}/statement/",         ["GET"]),
    ("ledger-balance",        f"/api/ledger/accounts/{_DUMMY_STR}/balance/",           ["GET"]),
    ("ledger-charges",        "/api/ledger/charges/",                                  ["POST"]),
    ("ledger-void-charge",    f"/api/ledger/charges/{_DUMMY_STR}/void/",               ["POST"]),
    ("ledger-open-charges",   "/api/ledger/charges/open/",                             ["GET"]),
    ("ledger-payments",       "/api/ledger/payments/",                                 ["POST"]),
    ("ledger-void-payment",   f"/api/ledger/payments/{_DUMMY_STR}/void/",              ["POST"]),
    ("ledger-allocate",       f"/api/ledger/payments/{_DUMMY_STR}/allocate/",          ["POST"]),
    ("ledger-open-invoices",  "/api/ledger/invoices/open/",                            ["GET"]),
    ("ledger-invariants",     "/api/ledger/invariants/",                               ["GET"]),

    # ── Academics ────────────────────────────────────────────────────────────
    ("academics-courses",     "/api/academics/courses/",                               ["GET"]),
    ("academics-sections",    "/api/academics/sections/",                              ["GET"]),
    ("academics-enroll",      "/api/academics/enroll/",                                ["POST"]),
    ("section-roster",        f"/api/academics/sections/{_DUMMY_STR}/roster/",         ["GET"]),

    # ── Billing ──────────────────────────────────────────────────────────────
    ("billing-runs",          "/api/billing/runs/",                          ["GET", "POST"]),
    ("billing-invoices",      "/api/billing/invoices/",                      ["GET"]),
    ("billing-installments",  "/api/billing/installment-plans/",             ["GET"]),
    ("household-billing",     f"/api/households/{_DUMMY_UUID}/billing/summary/", ["GET"]),

    # ── Terms / Scheduling ────────────────────────────────────────────────────
    ("terms-list",            "/api/terms/",                                     ["GET"]),
    ("term-sections",         f"/api/terms/{_DUMMY_UUID}/sections/",              ["GET"]),

    # ── Communications ────────────────────────────────────────────────────────
    ("threads-list",          "/api/threads/",                                   ["GET"]),
    ("thread-detail",         f"/api/threads/{_DUMMY_UUID}/",                    ["GET"]),
]


# ── Runner ────────────────────────────────────────────────────────────────────
def main() -> int:
    errors: list[str] = []
    checked = 0

    for label, path, methods in CONTRACT:
        errs = check(label, path, methods)
        errors.extend(errs)
        checked += 1

    if errors:
        print(f"\nContract Gate FAILED ({len(errors)} violation(s) / {checked} checked):\n")
        for e in errors:
            print(f"  ✗  {e}")
        return 1

    print(f"\nContract Gate PASSED  ({checked} endpoints verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
