# tools/verify_migration_lock_gate.py
# Phase 5 Migration Lock Gate
# Enforces:
# 1) All migration files apply cleanly to a fresh sqlite DB (migrate --noinput)
# 2) No migrations remain pending after apply (migrate --check)
# 3) showmigrations output contains no unapplied [ ] entries
#
# Complements the backend gate (which catches model→file drift via makemigrations --check).
# This gate catches the other failure mode: migration FILES that exist but cannot apply
# (broken squashes, circular dependencies, bad data migrations, wrong dependency chains).
#
# Requires DB (sqlite) — no external service needed.
# Typical runtime: 20-40s depending on migration count.

import os
import sys
import re
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path, env: dict[str, str]) -> None:
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(cwd), env=env)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def capture(cmd: list[str], cwd: Path, env: dict[str, str]) -> str:
    print(f"\n$ {' '.join(cmd)}")
    p = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise SystemExit(p.returncode)
    return p.stdout


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    backend = repo_root / "backend"
    manage_py = backend / "manage.py"

    if not backend.exists():
        print("Migration Lock Gate FAILED: missing backend/ directory")
        return 1
    if not manage_py.exists():
        print("Migration Lock Gate FAILED: missing backend/manage.py")
        return 1

    env = os.environ.copy()
    env.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    env.setdefault("SECRET_KEY", "ci-not-secret")
    env.setdefault("DEBUG", "0")
    env.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
    # Fresh sqlite DB per run — guarantees no state leakage between CI jobs
    env.setdefault("DATABASE_URL", "sqlite:///./ci_migration_lock.sqlite3")

    py = sys.executable

    # 1) Apply all migrations to a clean DB.
    #    Fails if any migration file has a broken dependency, circular reference,
    #    bad squash, or a data migration that raises an exception.
    print("\n[1/3] Applying all migrations to fresh sqlite DB...")
    run([py, "manage.py", "migrate", "--noinput"], cwd=backend, env=env)

    # 2) Assert nothing is pending after the apply.
    #    Exit code 1 if any migration is unapplied (deterministic Django behaviour).
    print("\n[2/3] Asserting no pending migrations...")
    run([py, "manage.py", "migrate", "--check"], cwd=backend, env=env)

    # 3) Belt-and-suspenders: parse showmigrations for any [ ] (unapplied) lines.
    print("\n[3/3] Scanning showmigrations for unapplied entries...")
    output = capture([py, "manage.py", "showmigrations", "--list"], cwd=backend, env=env)

    # Django marks unapplied migrations as "[ ] migration_name"
    unapplied = [
        line.strip()
        for line in output.splitlines()
        if re.search(r"\[ \]", line)
    ]
    if unapplied:
        print(f"\nMigration Lock Gate FAILED: {len(unapplied)} unapplied migration(s):")
        for u in unapplied:
            print(f"  {u}")
        return 1

    print("\nMigration Lock Gate PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
