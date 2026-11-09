"""Rehearse the exact reviewed 24-node DEV graph on a disposable PG15 restore.

This module has no DEV connection, Azure login or live-apply mode. Row contents
and process exception text never leave the child. Default deployment stays closed.
"""
from __future__ import annotations

import hashlib
from collections import Counter
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
STANDALONE_CARE_MIGRATION_SHA256 = "c4e6f05d1c3c4a13f51beeccbc960ae6cf0e9d5a808360436b2bf7f23789ab6f"

# Content-addressed public migration digests, separate from permission-named keys.
# This avoids falsely classifying file integrity pins as API credentials.
_TEACHER_EVALUATION_SHA256 = (
    "c9ea926404d37cd931644a230865c624497585e650b6b835b41be53d72e51531",
    "148d54455eb7b9e505bc40009abe87fca0507c21c9ba7f0d4e16f2cf2a4820ce",
    "61574a8596351919de7ac7ddb80fe45c45cb41ab2a81db74b62d954f9b1bbf73",
)
MIGRATIONS = {
    "core.0019_seed_summer_camp_permissions": "6a1b145b18725205749a031148166e1b08bd1b6fe8c22abeab2d3f138a21e9c0",
    "core.0020_diadem_daycare_staff_roles": "a106a5be72fd043ae3a644cd29bd143c98223ab03581ed3cfbca9bf42528038a",
    "core.0021_diadem_custody_release_permission": "8e60f050adaa248ba70258a4d0cac331c29f6c6ac18c669ca1c202a2d43767a3",
    "aftercare.0007_care_session_am_pm": "f33c18496abe641c35bb2691643f1a16b0bec132e180de912ec36dd6d7b46c99",
    "aftercare.0008_diadem_daycare_foundation": "c841ae0c7576ef0d8ab80f21019e8b93a31d9ada6f904753e8d79c8b8a41fe08",
    "aftercare.0009_diadem_checkin_foundation": "c9a7a6b17a6a256e28a1eacac14058e074a92f03bc1d3d967d0b490b11abf4fc",
    "aftercare.0010_diadem_custody_release": "46114fa788f1b5cdba733d8a6678584f9b36aa7200e21e6f751c11796b79651c",
    "aftercare.0011_aftercare_pickup_verified_by": "60e2a9cba39e09fd0799ea92c41808febdfb9b22a711794ed92828e75761415a",
    "aftercare.0012_diadem_visit_reentry_foundation": "40202de967e44e934cd24b21d61d832ecd28c2e3b719723b72c07ed7681e02c3",
    "aftercare.0013_daycare_setup_proposals": "eb32b6b6e52cbc18fe86f09621b8486db394168036f4283b6661bc651ac29cb0",
    "applications.0012_admissionssubmissionreceipt": "d90d68d448e36fdaabe702d894c67839a7f38fafe7e4b6a9e68f7a8d28294ccd",
    "core.0022_diadem_configuration_permission": "13bf4419d9e4168c20ab6bc4fc26c6d89c79a1ce616296674b7643f50a92f4f3",
    "integrations.0003_microsoft_identity_binding": "851df18652815eb197dae6acee8851ae8667ac5475bf54e0e2fcbde59536a3e1",
    "jireh_sgo.0002_fictional_family_intake": "08817b858d9f863024bbdc4e296a407765f7ded649ff395a6b494a0df17e600e",
    "sandbox_demo.0005_sandboxbuyerworkspace": "7d83346019abd52600c172361c69eababbeb3735783bc0e695324a01ed3b5722",
    "sandbox_demo.0006_hosted_jireh_bindings": "d6b31c7ede84977e3a5b28c6460139e779577756722103ca5e73324a9e6b3aa7",
    "subscriptions.0006_alter_schoolmodule_module_key_standalone_care": STANDALONE_CARE_MIGRATION_SHA256,
    "summer_camp.0002_pickup_verification_actor": "37ac05a32e08b1a6bc8489998e0dcc56dc71a131c68f2768d2378b62df954d25",
    "summer_camp.0003_staff_credential_review_evidence": "ff7104d13428987d47a593b6144372884a1028571e442ea74753486aeb1c46a2",
    "aftercare.0014_legacy_insert_defaults": "56e5452016ee85b3f1a22a9a0b79be1560b2aba5476287a6447f4931cf750966",
    "summer_camp.0004_legacy_insert_defaults": "b23f86034769d9cd676522a68f5b22bd291457d3563e7c13b76586329243a2a8",
    "teacher_evaluations.0001_initial": _TEACHER_EVALUATION_SHA256[0],
    "teacher_evaluations.0002_access_events": _TEACHER_EVALUATION_SHA256[1],
    "teacher_evaluations.0003_order_access_decisions": _TEACHER_EVALUATION_SHA256[2],
}
SEED_TABLES = {"core_crownpermission", "core_rolepermission", "subscriptions_feature"}
DB_NAME = re.compile(r"crown_restore_[0-9]{1,20}_[0-9]{1,5}\Z")


class RehearsalBlocked(RuntimeError):
    """Only fixed non-sensitive reason codes are emitted."""


def verify_manifest(root=ROOT):
    for identity, digest in MIGRATIONS.items():
        app, name = identity.split(".", 1)
        path = root / "backend" / app / "migrations" / (name + ".py")
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RehearsalBlocked("reviewed_migration_source_mismatch")


def verify_plan(plan):
    identities = [item.app_label + "." + item.name for item, _ in plan]
    if (any(backwards for _, backwards in plan) or len(identities) != len(MIGRATIONS)
            or set(identities) != set(MIGRATIONS)):
        raise RehearsalBlocked("restored_pending_graph_differs")
    # Independent migrations may have a different topological ordering.
    return identities


def validate_target(database, actual_database, user, version, cluster, expected_cluster):
    if (not isinstance(database, str) or not DB_NAME.fullmatch(database)
            or actual_database != database or user != "crown_drill"
            or not isinstance(version, int) or isinstance(version, bool) or version // 10000 != 15
            or not isinstance(expected_cluster, str) or not re.fullmatch(r"[0-9]{1,24}", expected_cluster)
            or str(cluster) != expected_cluster):
        raise RehearsalBlocked("disposable_pg15_identity_mismatch")


def child_environment(database, port, cluster, source_sha, environ):
    if (not isinstance(database, str) or not DB_NAME.fullmatch(database)
            or not isinstance(port, str) or not port.isdigit() or not 1 <= int(port) <= 65535
            or not isinstance(cluster, str) or not re.fullmatch(r"[0-9]{1,24}", cluster)
            or not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha)):
        raise RehearsalBlocked("disposable_pg15_connection_invalid")
    # No source URL, signing secret, Azure identity or inherited PG selector.
    result = {key: environ[key] for key in ("PATH", "HOME") if key in environ}
    result.update(
        DATABASE_URL=f"postgresql://crown_drill:crown-drill-password@127.0.0.1:{port}/{database}?sslmode=disable",
        DJANGO_SETTINGS_MODULE="crown_api.settings", DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        CROWN_ENV="dev", DJANGO_ENV="development", DEBUG="false", DJANGO_DEBUG="false",
        BUILD_SHA=source_sha, CROWN_DEMO_MODE="false", CROWN_SIMPLEJWT_BLACKLIST_ENABLED="false",
        CROWN_SANDBOX_ALLOW_OPEN_SESSION="false", ALLOWED_HOSTS="localhost,127.0.0.1,testserver",
        CROWN_REHEARSAL_DATABASE=database, CROWN_REHEARSAL_CLUSTER=cluster,
        PYTHONPATH=str(ROOT / "backend") + os.pathsep + str(ROOT),
    )
    return result


def rehearse_clone(database, port, cluster, source_sha, environ, *, run=subprocess.run):
    verify_manifest()
    env = child_environment(database, port, cluster, source_sha, environ)
    try:
        result = run([sys.executable, str(Path(__file__).resolve()), "--clone"],
                     cwd=ROOT, env=env, capture_output=True, text=True, timeout=900, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise RehearsalBlocked("clone_migration_rehearsal_failed") from None
    try:
        lines = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    except (ValueError, TypeError):
        raise RehearsalBlocked("clone_rehearsal_receipt_invalid") from None
    receipt = lines[0] if len(lines) == 1 and isinstance(lines[0], dict) else {}
    if (result.returncode or receipt.get("result") != "PASS"
            or receipt.get("source_sha") != source_sha or receipt.get("remaining_pending") != 0
            or type(receipt.get("remaining_pending")) is not int
            or receipt.get("reviewed_migrations") != len(MIGRATIONS)
            or receipt.get("target_postgres_major") != 15
            or type(receipt.get("baseline_migration_records")) is not int
            or receipt.get("baseline_migration_records", 0) < 1
            or type(receipt.get("baseline_public_tables")) is not int
            or receipt.get("baseline_public_tables", 0) < 1
            or not isinstance(receipt.get("baseline_fingerprint"), str)
            or not re.fullmatch(r"[0-9a-f]{64}", receipt.get("baseline_fingerprint", ""))
            or receipt.get("migrated_records") != receipt.get("baseline_migration_records", 0) + len(MIGRATIONS)
            or receipt.get("existing_seed_rows_preserved") is not True
            or receipt.get("existing_nonseed_table_values_preserved") is not True
            or receipt.get("existing_table_counts_preserved") is not True
            or receipt.get("atomic_graph") is not True or receipt.get("legacy_inserts_preserved") is not True
            or receipt.get("live_schema_write_performed") is not False):
        reason = receipt.get("reason")
        if reason not in {"restored_pending_graph_differs", "disposable_pg15_identity_mismatch",
                          "reviewed_migration_source_mismatch", "existing_data_changed",
                          "migration_history_changed", "clone_migration_failed", "legacy_insert_contract_failed"}:
            reason = "clone_migration_rehearsal_failed"
        error = RehearsalBlocked(reason)
        error.receipt = dict(result="BLOCKED", source_sha=source_sha, reason=reason)
        if receipt.get("migration") in MIGRATIONS:
            error.receipt["migration"] = receipt["migration"]
        if isinstance(receipt.get("sqlstate"), str) and re.fullmatch(r"[0-9A-Z]{5}", receipt["sqlstate"]):
            error.receipt["sqlstate"] = receipt["sqlstate"]
        raise error
    return lines[0]


def table_facts(connection):
    """Hash old column values privately; publish only a preservation Boolean."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT c.table_name,c.column_name FROM information_schema.columns c "
                       "JOIN information_schema.tables t ON t.table_schema=c.table_schema "
                       "AND t.table_name=c.table_name WHERE c.table_schema='public' "
                       "AND t.table_type='BASE TABLE' ORDER BY c.table_name,c.ordinal_position")
        columns = {}
        for table, column in cursor.fetchall():
            columns.setdefault(table, []).append(column)
    return columns


def row_digest(connection, table, columns):
    quote = connection.ops.quote_name
    digest, count = hashlib.sha256(), 0
    with connection.cursor() as cursor:
        cursor.execute("SELECT row_to_json(t)::text FROM (SELECT " +
                       ",".join(quote(c) for c in columns) + " FROM public." + quote(table) +
                       ') t ORDER BY (row_to_json(t)::text) COLLATE "C"')
        while rows := cursor.fetchmany(500):
            for (value,) in rows:
                raw = value.encode()
                digest.update(str(len(raw)).encode() + b":" + raw)
                count += 1
    return count, digest.hexdigest()


def seed_row_multiset(connection, table, columns):
    """Preserve every preexisting seed row; reviewed migrations may ADD rows.

    A row-count-only check misses updates to existing permission or feature
    records. Preserve a multiset of hashes over the original column projection,
    including duplicate records, without publishing data or raw row values.
    """
    quote = connection.ops.quote_name
    counts = Counter()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT row_to_json(t)::text FROM (SELECT " +
            ",".join(quote(c) for c in columns) + " FROM public." +
            quote(table) + ") t"
        )
        while rows := cursor.fetchmany(500):
            counts.update(hashlib.sha256(value.encode()).digest() for (value,) in rows)
    return counts


def data_fingerprint(columns, rows):
    """Source/clone comparison receipt; no row contents leave the process."""
    return hashlib.sha256(json.dumps({"columns": columns, "rows": rows}, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def verify_legacy_writes(executor, connection):
    """Probe previous model INSERTs in a rolled-back clone-only savepoint."""
    from datetime import date, datetime, time
    from uuid import uuid4
    from django.db import transaction
    from django.utils import timezone

    excluded = {tuple(x.split(".", 1)) for x in MIGRATIONS}
    targets = [key for key, node in executor.loader.graph.node_map.items() if key not in excluded
               and not any(child.key not in excluded for child in node.children)]
    old = executor.loader.project_state(targets).apps
    try:
        with transaction.atomic(using=connection.alias):
            school = old.get_model("core", "School").objects.create(name="Fictional legacy INSERT probe")
            household = old.get_model("households", "Household").objects.create(school_id=school.pk, name="Fictional Probe")
            child = old.get_model("households", "Student").objects.create(
                school_id=school.pk, household=household, first_name="Fictional", last_name="Probe", grade_level="4")
            old.get_model("aftercare", "AftercareAttendance").objects.create(
                school_fk_id=school.pk, student_fk_id=child.pk, date=date(2025, 9, 4),
                checkin_time=timezone.make_aware(datetime(2025, 9, 4, 15)), pickup_verified=False)
            old.get_model("aftercare", "AftercareProgramConfig").objects.create(school_fk_id=school.pk)
            old.get_model("aftercare", "AftercareEnrollment").objects.create(
                school_fk_id=school.pk, student_fk_id=child.pk, start_date=date(2025, 9, 4), billing_model="FLAT_MONTHLY")
            user = old.get_model("core", "UserAccount").objects.create(
                school_id=school.pk, username="fictional-migration-" + uuid4().hex,
                email=uuid4().hex + "@example.invalid", password="!")
            program = old.get_model("summer_camp", "SummerCampProgram").objects.create(school_id=school.pk, name="Fictional Probe")
            session = old.get_model("summer_camp", "SummerCampSession").objects.create(
                school_id=school.pk, program=program, name="Fictional Probe", start_date=date(2025, 7, 1),
                end_date=date(2025, 7, 2), start_time=time(8), end_time=time(15))
            old.get_model("summer_camp", "SummerCampStaffAssignment").objects.create(
                school_id=school.pk, session=session, staff_user=user, role="Fictional probe", credential_status="PENDING")
            daycare = executor.loader.project_state([("aftercare", "0012_diadem_visit_reentry_foundation")]).apps
            daycare.get_model("aftercare", "DaycareSite").objects.create(
                school_id=school.pk, code="fictional-" + uuid4().hex[:8], name="Fictional legacy probe", is_active=False)
            transaction.set_rollback(True, using=connection.alias)
    except Exception as exception:
        error = RehearsalBlocked("legacy_insert_contract_failed")
        error.sqlstate = getattr(exception.__cause__, "sqlstate", None)
        raise error from None


def migrate_restored_copy():
    import django
    django.setup()
    from django.db import connection, transaction
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.recorder import MigrationRecorder

    database = os.environ["CROWN_REHEARSAL_DATABASE"]
    if connection.vendor != "postgresql" or connection.settings_dict["HOST"] != "127.0.0.1":
        raise RehearsalBlocked("disposable_pg15_identity_mismatch")
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(),current_user,current_setting('server_version_num')::int")
        actual, user, version = cursor.fetchone()
        cursor.execute("SELECT system_identifier FROM pg_control_system()")
        cluster = cursor.fetchone()[0]
    validate_target(database, actual, user, version, cluster, os.environ["CROWN_REHEARSAL_CLUSTER"])
    verify_manifest()
    active_migration = None
    def progress(action, migration=None, fake=False):
        nonlocal active_migration
        if action == "apply_start" and migration is not None:
            active_migration = migration.app_label + "." + migration.name
    executor = MigrationExecutor(connection, progress_callback=progress)
    executor.loader.check_consistent_history(connection)
    targets = executor.loader.graph.leaf_nodes()
    planned = verify_plan(executor.migration_plan(targets))
    before_history = set(MigrationRecorder(connection).applied_migrations())
    columns = table_facts(connection)
    baseline = {table: row_digest(connection, table, names) for table, names in columns.items()}
    seed_baseline = {
        table: seed_row_multiset(connection, table, columns[table])
        for table in SEED_TABLES if table in columns
    }
    with transaction.atomic(using=connection.alias):
        try:
            executor.migrate(targets)
        except Exception as exception:
            error = RehearsalBlocked("clone_migration_failed")
            error.migration = active_migration
            error.sqlstate = getattr(exception.__cause__, "sqlstate", None)
            raise error from None
        remaining = MigrationExecutor(connection).migration_plan(targets)
        after_history = set(MigrationRecorder(connection).applied_migrations())
        expected_history = before_history | {tuple(x.split(".", 1)) for x in planned}
        if remaining or after_history != expected_history:
            raise RehearsalBlocked("migration_history_changed")
        for table, names in columns.items():
            after = row_digest(connection, table, names)
            if table == "django_migrations":
                if after[0] != baseline[table][0] + len(planned):
                    raise RehearsalBlocked("migration_history_changed")
            elif table in SEED_TABLES:
                if seed_baseline[table] - seed_row_multiset(connection, table, names):
                    raise RehearsalBlocked("existing_data_changed")
            elif after != baseline[table]:
                raise RehearsalBlocked("existing_data_changed")
        verify_legacy_writes(executor, connection)
        return dict(result="PASS", source_sha=os.environ["BUILD_SHA"], target_postgres_major=15,
                    reviewed_migrations=len(planned), remaining_pending=0,
                    baseline_migration_records=len(before_history), migrated_records=len(after_history),
                    baseline_fingerprint=data_fingerprint(columns, baseline), baseline_public_tables=len(columns),
                    existing_nonseed_table_values_preserved=True, existing_seed_rows_preserved=True,
                    existing_table_counts_preserved=True,
                    live_schema_write_performed=False, atomic_graph=True, legacy_inserts_preserved=True)


if __name__ == "__main__":
    try:
        if sys.argv[1:] != ["--clone"]:
            raise RehearsalBlocked("clone_entry_required")
        outcome = migrate_restored_copy()
    except Exception as error:
        outcome = {"result": "BLOCKED", "reason": str(error) if isinstance(error, RehearsalBlocked)
                   else "clone_migration_rehearsal_failed"}
        if getattr(error, "migration", None) in MIGRATIONS:
            outcome["migration"] = error.migration
        code = getattr(error, "sqlstate", None)
        if isinstance(code, str) and re.fullmatch(r"[0-9A-Z]{5}", code):
            outcome["sqlstate"] = code
    print(json.dumps(outcome, sort_keys=True))
    raise SystemExit(0 if outcome["result"] == "PASS" else 1)
