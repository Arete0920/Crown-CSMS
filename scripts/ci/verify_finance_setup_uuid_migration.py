"""Exercise Finance Setup integer-to-UUID-compatible schema on disposable CI PostgreSQL.

This command is deliberately incompatible with a hosted database. It checks the
GitHub Actions marker, exact CI database name/host, and PostgreSQL vendor before
any migration or fixture write. It changes only the job-local finance_ci database.
"""
from __future__ import annotations

import os
from uuid import uuid4

import django
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

PREVIOUS = "0002_alter_discountpolicy_max_discount_percent_bp_and_more"
CURRENT = "0003_financepolicyversion_uuid_compatible_school_id"
YEAR = "2026-2027"
LEGACY_ID = 41


def _require_disposable_database() -> None:
    database = connection.settings_dict
    if (
        os.environ.get("GITHUB_ACTIONS", "").lower() != "true"
        or connection.vendor != "postgresql"
        or database.get("NAME") != "finance_ci"
        or database.get("HOST") not in {"localhost", "127.0.0.1"}
        or database.get("USER") != "finance_ci"
    ):
        raise RuntimeError("Finance Setup migration proof requires job-local finance_ci PostgreSQL")


def _actual_school_id_type() -> str:
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT data_type FROM information_schema.columns
               WHERE table_schema = current_schema()
                 AND table_name = %s AND column_name = %s""",
            ["finance_setup_financepolicyversion", "school_id"],
        )
        row = cursor.fetchone()
        if row is None:
            raise AssertionError("finance_setup_financepolicyversion.school_id missing")
        return str(row[0])


def _legacy_row(row_id: int, expected_school_id: str) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """SELECT school_id::text, academic_year, is_locked, locked_by
               FROM finance_setup_financepolicyversion WHERE id = %s""",
            [row_id],
        )
        actual = cursor.fetchone()
    assert actual == (expected_school_id, YEAR, True, "legacy-synthetic-lock"), (
        "Finance Setup migration changed historical policy identity or lock evidence",
        actual,
    )


def main() -> None:
    django.setup()
    _require_disposable_database()

    # Start with the actual old persisted schema. No live school is created or
    # inferred from legacy numeric IDs; this is a synthetic, isolated database.
    call_command("migrate", "finance_setup", PREVIOUS, interactive=False, verbosity=0)
    assert _actual_school_id_type() == "integer"

    locked_at = timezone.now()
    with connection.cursor() as cursor:
        cursor.execute(
            """INSERT INTO finance_setup_financepolicyversion
               (school_id, academic_year, is_locked, locked_at, locked_by, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
            [LEGACY_ID, YEAR, True, locked_at, "legacy-synthetic-lock", locked_at, locked_at],
        )
        row_id = cursor.fetchone()[0]

    _legacy_row(row_id, str(LEGACY_ID))
    call_command("migrate", "finance_setup", CURRENT, interactive=False, verbosity=0)
    assert _actual_school_id_type() == "character varying"
    _legacy_row(row_id, str(LEGACY_ID))

    # A real canonical UUID must coexist with the preserved legacy text key
    # without aliasing it. This proves the column supports full UUID identities.
    from finance_setup.models import FinancePolicyVersion

    school_id = str(uuid4())
    uuid_policy = FinancePolicyVersion.objects.create(
        school_id=school_id, academic_year=YEAR,
    )
    uuid_policy.refresh_from_db()
    assert uuid_policy.school_id == school_id
    assert FinancePolicyVersion.objects.filter(school_id=str(LEGACY_ID), academic_year=YEAR).count() == 1
    assert FinancePolicyVersion.objects.filter(school_id=school_id, academic_year=YEAR).count() == 1

    # Roll back only after removing the synthetic UUID row. A real deployment
    # with UUID policies MUST NOT reverse this migration without reviewed data
    # reconciliation; we never attempt to coerce UUID strings into integers.
    uuid_policy.delete()
    call_command("migrate", "finance_setup", PREVIOUS, interactive=False, verbosity=0)
    assert _actual_school_id_type() == "integer"
    _legacy_row(row_id, str(LEGACY_ID))
    call_command("migrate", "finance_setup", CURRENT, interactive=False, verbosity=0)
    assert _actual_school_id_type() == "character varying"
    _legacy_row(row_id, str(LEGACY_ID))
    print("PASS: old locked row retained across migration, UUID supported, and legacy-only rollback reversible")


if __name__ == "__main__":
    main()
