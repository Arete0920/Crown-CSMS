# tools/verify_backend_gate.py
# Phase 5 Backend Gate (static/runtime checks)
# Enforces:
# 1) Python bytecode compile of backend/ (compileall)
# 2) Django system checks (manage.py check)
# 3) Migration drift check (makemigrations --check --dry-run)
#
# Designed to be deterministic in CI by setting safe env defaults.
# No DB connection required for these checks.

import os
import sys
import subprocess
from pathlib import Path

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
        print("Backend Gate FAILED: missing backend/ directory")
        return 1
    if not manage_py.exists():
        print("Backend Gate FAILED: missing backend/manage.py")
        return 1

    env = os.environ.copy()

    # Deterministic CI defaults (safe for check/compile/migrations)
    env.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    env.setdefault("SECRET_KEY", "ci-not-secret")
    env.setdefault("DEBUG", "0")
    env.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
    # If the project uses dj-database-url, this prevents accidental external DB dependency.
    env.setdefault("DATABASE_URL", "sqlite:///./ci.sqlite3")

    py = sys.executable

    # 1) Compile all Python under backend/
    run([py, "-m", "compileall", "-q", "backend"], cwd=repo_root, env=env)

    # 2) Django system checks (non-deploy; keep deterministic)
    run([py, "manage.py", "check"], cwd=backend, env=env)

    # 3) Migration drift check (fails if model changes not captured in migrations)
    run([py, "manage.py", "makemigrations", "--check", "--dry-run"], cwd=backend, env=env)

    print("\nBackend Gate PASSED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
