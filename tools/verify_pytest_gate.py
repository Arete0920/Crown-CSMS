# tools/verify_pytest_gate.py
# Phase 5 Pytest Gate (curated fast test set)
# Enforces:
# 1) Core RBAC contract
# 2) Tenant enforcement / header guards / write guards
# 3) Ledger invariants + immutability + write safety
# 4) Journal invariants
# 5) Import sanity + health endpoint
#
# Runs against sqlite in CI - no external DB required.
# All tests in this set must remain fast (< 60s total).

import os
import sys
import subprocess
from pathlib import Path

# Curated fast test set: core + RBAC + ledger invariants
FAST_TEST_PATHS = [
    # Required regression proof for the repaired trust boundary
    "backend/core/tests/test_explicit_permission_authority.py",
    "backend/core/tests/test_tenant_persistence_authority.py",
    "backend/ledger/tests/test_financial_fact_boundaries.py",
    "backend/core/tests/test_schema_deployment_contract.py",
    "backend/core/tests/test_runtime_admin_bootstrap.py",
    # RBAC / auth / tenant
    "backend/core/tests/test_rbac_contract.py",
    "backend/crown_api/tests/test_rbac_proof.py",
    "backend/crown_api/tests/test_gate1c_auth_tenant_proof.py",
    "backend/crown_api/tests/test_tenant_enforcement.py",
    "backend/tests/test_tenant_header_required.py",
    "backend/tests/test_tenant_write_guard.py",
    # Ledger invariants
    "backend/ledger/tests/test_ledger_invariants.py",
    "backend/ledger/tests/test_ledger_immutability.py",
    "backend/ledger/tests/test_ledger_write_safety.py",
    "backend/journal/tests/test_journal_invariants.py",
    # Import sanity + health
    "backend/tests/test_import_sanity.py",
    "backend/crown_api/tests/test_health.py",
]


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(cwd), env=env)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    backend = repo_root / "backend"
    manage_py = backend / "manage.py"

    if not backend.exists():
        print("Pytest Gate FAILED: missing backend/ directory")
        return 1
    if not manage_py.exists():
        print("Pytest Gate FAILED: missing backend/manage.py")
        return 1

    # Verify all test files exist before wasting time migrating
    missing = [p for p in FAST_TEST_PATHS if not (repo_root / p).exists()]
    if missing:
        print("Pytest Gate FAILED: missing test files:")
        for m in missing:
            print(f"  {m}")
        return 1

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    env.setdefault("SECRET_KEY", "ci-not-secret")
    env.setdefault("DEBUG", "0")
    env.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
    env.setdefault("DATABASE_URL", "sqlite:///./ci.sqlite3")

    py = sys.executable

    # Migrate to ensure test DB schema is current
    run([py, "manage.py", "migrate", "--noinput"], cwd=backend, env=env)

    # Run curated fast test set
    run(
        [py, "-m", "pytest", "-ra", "--tb=short", "--no-header"] + FAST_TEST_PATHS,
        cwd=repo_root,
        env=env,
    )

    print("\nPytest Gate PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
