from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path


LOCK_ID = 2026071701
EXPECTED_TIMEOUT = "Timed out waiting for the production schema migration lock"


def run_competing_migration(backend: Path, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "manage.py",
            "migrate_with_lock",
            "--check",
            "--lock-timeout-seconds",
            str(timeout_seconds),
            "--verbosity",
            "1",
        ],
        cwd=backend,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    backend = repo_root / "backend"
    sys.path.insert(0, str(backend))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")

    import django

    django.setup()

    from django.db import connection

    if connection.vendor != "postgresql":
        print(
            "PostgreSQL migration lock contention proof FAILED: "
            f"database vendor is {connection.vendor!r}"
        )
        return 1

    acquired = False
    released = False
    elapsed = 0.0
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
            acquired = bool(cursor.fetchone()[0])
            if not acquired:
                print(
                    "PostgreSQL migration lock contention proof FAILED: "
                    "holder could not acquire lock"
                )
                return 1

            started = time.monotonic()
            competitor = run_competing_migration(backend, timeout_seconds=2)
            elapsed = time.monotonic() - started

            combined_output = f"{competitor.stdout}\n{competitor.stderr}"
            if competitor.returncode == 0:
                print(combined_output)
                print(
                    "PostgreSQL migration lock contention proof FAILED: "
                    "competitor acquired lock"
                )
                return 1
            if EXPECTED_TIMEOUT not in combined_output:
                print(combined_output)
                print(
                    "PostgreSQL migration lock contention proof FAILED: "
                    "unexpected competitor error"
                )
                return 1
            if elapsed < 1.5:
                print(combined_output)
                print(
                    "PostgreSQL migration lock contention proof FAILED: "
                    f"competitor rejected too quickly ({elapsed:.2f}s)"
                )
                return 1
    finally:
        if acquired:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [LOCK_ID])
                released = bool(cursor.fetchone()[0])

    if acquired and not released:
        print(
            "PostgreSQL migration lock contention proof FAILED: "
            "holder did not release lock"
        )
        return 1

    successor = run_competing_migration(backend, timeout_seconds=5)
    if successor.returncode != 0:
        print(successor.stdout)
        print(successor.stderr)
        print(
            "PostgreSQL migration lock contention proof FAILED: "
            "successor could not acquire lock"
        )
        return 1

    if "schema migration authority acquired; vendor=postgresql" not in successor.stdout:
        print(successor.stdout)
        print(successor.stderr)
        print(
            "PostgreSQL migration lock contention proof FAILED: "
            "acquisition evidence missing"
        )
        return 1

    print(
        "PostgreSQL migration lock contention proof PASSED: "
        f"competitor timed out after {elapsed:.2f}s and successor acquired the released lock"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
