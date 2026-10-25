"""Restore an authorized synthetic DEV snapshot only inside the CI PostgreSQL service.

No archive, credentials, row contents, or process error text enters evidence.
The source session and pg_dump are read-only. Every write uses docker exec on
the pinned job service, explicit loopback connection settings and a unique DB.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time
from urllib.parse import unquote, urlsplit

from read_dev_blacklist_state import read_dev_database_setting, verify_accepted_source
from run_dev_inquiry_migration import DEV_APP, DEV_HOST, validate_database_url

SOURCE_IDENTITY = "fb4bfe404d7d9b1f6f9c91b12d906f6b2b23be5e16792e7a6af6642cbf5d2eb7"
CA = "/etc/ssl/certs/ca-certificates.crt"
IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
CONFIRMATION = "restore-dev-backup-in-ci"


class RestoreBlocked(RuntimeError):
    """Only fixed codes may leave this module."""


def now():
    return datetime.now(timezone.utc).isoformat()


def authority(expected_sha, confirmation, synthetic, environ):
    if (not re.fullmatch(r"[0-9a-f]{40}", expected_sha)
            or confirmation != CONFIRMATION or synthetic != "true"
            or environ.get("GITHUB_ACTIONS") != "true"
            or environ.get("GITHUB_REF") != "refs/heads/main"
            or environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch"):
        raise RestoreBlocked("explicit_dev_restore_authority_required")
    container = environ.get("POSTGRES_CONTAINER_ID", "")
    run_id, attempt = environ.get("GITHUB_RUN_ID", ""), environ.get("GITHUB_RUN_ATTEMPT", "")
    if (not re.fullmatch(r"[0-9a-f]{12,64}", container)
            or not re.fullmatch(r"[0-9]{1,20}", run_id)
            or not re.fullmatch(r"[0-9]{1,5}", attempt)):
        raise RestoreBlocked("ci_restore_target_unverified")
    return container, f"crown_restore_{run_id}_{attempt}"


def clean_environment(environ):
    # Never inherit libpq service/host/password/options or Django/Azure secrets.
    return {key: environ[key] for key in ("PATH", "HOME") if key in environ}


def source_environment(url, database, environ):
    if validate_database_url(url) != database:
        raise RestoreBlocked("source_database_mismatch")
    identity = hashlib.sha256((DEV_HOST + "/" + database).encode()).hexdigest()
    if identity != SOURCE_IDENTITY:
        raise RestoreBlocked("source_database_identity_changed")
    parsed = urlsplit(url)
    user, password = unquote(parsed.username or ""), unquote(parsed.password or "")
    if not user or not password or any(c in user + password for c in "\r\n\x00"):
        raise RestoreBlocked("source_credentials_unavailable")
    return {
        **clean_environment(environ), "PGHOST": DEV_HOST, "PGPORT": "5432",
        "PGUSER": user, "PGPASSWORD": password, "PGDATABASE": database,
        "PGSSLMODE": "verify-full", "PGSSLROOTCERT": CA,
        "PGCONNECT_TIMEOUT": "12",
        "PGOPTIONS": "-c default_transaction_read_only=on -c statement_timeout=300000",
    }


def target_environment(environ):
    return {
        **clean_environment(environ), "PGHOST": "127.0.0.1", "PGPORT": "5432",
        "PGUSER": "crown_drill", "PGPASSWORD": "crown-drill-password",
        "PGDATABASE": "postgres", "PGSSLMODE": "disable", "PGCONNECT_TIMEOUT": "12",
        "PGOPTIONS": "-c statement_timeout=300000 -c lock_timeout=10000",
    }


def docker_command(container, env, command):
    if not re.fullmatch(r"[0-9a-f]{12,64}", container):
        raise RestoreBlocked("ci_restore_target_unverified")
    args = ["docker", "--host", "unix:///var/run/docker.sock", "exec", "-i"]
    for key in sorted(env):
        if key.startswith("PG"):
            args.extend(["-e", key])  # Values stay in subprocess environment, never argv.
    return args + [container] + command


def classify_dump_failure(stderr: bytes) -> str:
    """Map raw pg_dump diagnostics to literal, non-sensitive evidence codes only.

    Never include stderr, connection parameters, object names or exception text
    in a returned value, artifact or public job output. Ambiguous failures stay
    unclassified rather than guessing the underlying problem.
    """
    detail = (stderr or b"")[:65536].decode("utf-8", errors="replace").lower()
    categories = (
        (r"(?:password authentication failed|fe_sendauth: no password supplied|no pg_hba\.conf entry)",
         "source_dump_authentication_blocked"),
        (r"(?:could not translate host name|connection timed out|connection refused|network is unreachable|could not connect to server)",
         "source_dump_connectivity_blocked"),
        (r"(?:certificate verify failed|ssl error|root certificate file)",
         "source_dump_tls_blocked"),
        (r"(?:server version mismatch|aborting because of server version mismatch)",
         "source_dump_client_version_blocked"),
        (r"(?:permission denied for|permission denied to|must be owner of)",
         "source_dump_read_permission_blocked"),
        (r"(?:invalid snapshot identifier|could not import snapshot|invalid snapshot|snapshot .* does not exist)",
         "source_dump_snapshot_blocked"),
    )
    matches = [code for pattern, code in categories if re.search(pattern, detail)]
    return matches[0] if len(matches) == 1 else "source_dump_unclassified_failure"


def execute(container, env, command, *, run=subprocess.run, stdin=None, stdout=None):
    try:
        result = run(docker_command(container, env, command), env=env, stdin=stdin,
                     stdout=stdout if stdout is not None else subprocess.PIPE,
                     stderr=subprocess.PIPE, timeout=600, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RestoreBlocked("postgres_process_unavailable") from exc
    if result.returncode:
        if command and command[0] == "pg_dump":
            raise RestoreBlocked(classify_dump_failure(result.stderr))
        raise RestoreBlocked("postgres_process_failed")
    return result.stdout or b""


def scalar(container, env, database, query):
    value = execute(container, env, ["psql", "-X", "-A", "-t", "--set=ON_ERROR_STOP=1",
                                   "--dbname", database, "--command", query])
    return value.decode().strip()


def target_identity(container, env):
    value = scalar(container, env, "postgres",
                   "SELECT current_database() || '|' || current_user || '|' || "
                   "host(inet_server_addr()) || '|' || current_setting('server_version_num')")
    pieces = value.split("|")
    if (len(pieces) != 4 or pieces[:3] != ["postgres", "crown_drill", "127.0.0.1"]
            or not pieces[3].isdigit() or not 160000 <= int(pieces[3]) < 170000):
        raise RestoreBlocked("disposable_postgres_identity_mismatch")


def read_snapshot(connection):
    """Hold a repeatable read-only snapshot through source counting and dump."""
    from psycopg import sql
    with connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
        cursor.execute("SHOW transaction_read_only")
        if cursor.fetchone() != ("on",):
            raise RestoreBlocked("source_transaction_not_read_only")
        cursor.execute("SELECT current_database(), current_schema(), pg_is_in_recovery(), "
                       "current_setting('server_version_num')::integer")
        database, schema, recovery, version = cursor.fetchone()
        if (hashlib.sha256((DEV_HOST + "/" + database).encode()).hexdigest() != SOURCE_IDENTITY
                or schema != "public" or recovery or not 130000 <= version < 170000):
            raise RestoreBlocked("connected_source_identity_mismatch")
        cursor.execute("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
        if cursor.fetchone() != (True,):
            raise RestoreBlocked("source_tls_not_verified")
        cursor.execute("SELECT pg_export_snapshot()")
        snapshot = cursor.fetchone()[0]
        snapshot_created_at = now()
        if not re.fullmatch(r"[0-9A-Fa-f-]{1,80}", snapshot):
            raise RestoreBlocked("snapshot_identity_invalid")
        cursor.execute("SELECT table_name FROM information_schema.tables "
                       "WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        if (not {"django_migrations", "core_school", "core_useraccount"}.issubset(tables)
                or any(not IDENTIFIER.fullmatch(name) for name in tables)):
            raise RestoreBlocked("source_tables_unverified")
        counts = {}
        for table in tables:
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM public.{}").format(sql.Identifier(table)))
            counts[table] = cursor.fetchone()[0]
        cursor.execute("SELECT table_name,column_name,data_type,is_nullable,column_default "
                       "FROM information_schema.columns WHERE table_schema='public' "
                       "ORDER BY table_name,ordinal_position")
        columns = cursor.fetchall()
        cursor.execute("SELECT app,name FROM django_migrations ORDER BY app,name")
        migrations = cursor.fetchall()
    return snapshot, counts, columns, migrations, version, snapshot_created_at


def target_facts(container, env, database, counts):
    restored = {}
    for table in counts:
        # Names were validated against a strict identifier grammar at source.
        restored[table] = int(scalar(container, env, database, f'SELECT COUNT(*) FROM public."{table}"'))
    columns = json.loads(scalar(container, env, database,
        "SELECT coalesce(json_agg(row_to_json(x)), '[]'::json) FROM "
        "(SELECT table_name,column_name,data_type,is_nullable,column_default "
        "FROM information_schema.columns WHERE table_schema='public' "
        "ORDER BY table_name,ordinal_position) x"))
    migrations = json.loads(scalar(container, env, database,
        "SELECT coalesce(json_agg(row_to_json(x)), '[]'::json) FROM "
        "(SELECT app,name FROM django_migrations ORDER BY app,name) x"))
    tables = int(scalar(container, env, database,
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema='public' AND table_type='BASE TABLE'"))
    return restored, [tuple(row.values()) for row in columns], [tuple(row.values()) for row in migrations], tables


@contextmanager
def disposable_database(container, env, database, evidence, *, action=execute):
    if not re.fullmatch(r"crown_restore_[0-9]{1,20}_[0-9]{1,5}", database):
        raise RestoreBlocked("restore_database_name_invalid")
    # Never remove a pre-existing database, including on an unsuccessful retry.
    exists = action(container, env, ["psql", "-X", "-A", "-t", "--set=ON_ERROR_STOP=1",
                    "--dbname", "postgres", "--command",
                    f"SELECT COUNT(*) FROM pg_database WHERE datname='{database}'"])
    if exists.decode().strip() != "0":
        raise RestoreBlocked("restore_database_already_exists")
    attempted = False
    try:
        attempted = True
        action(container, env, ["createdb", "--maintenance-db=postgres", database])
        evidence["disposable_database_created"] = True
        yield
    finally:
        if attempted:
            try:
                action(container, env, ["dropdb", "--maintenance-db=postgres", "--if-exists", "--force", database])
                evidence["disposable_database_dropped"] = True
            except Exception as exc:
                raise RestoreBlocked("disposable_database_cleanup_failed") from exc


def restore_archive(container, env, database, archive, facts, evidence):
    with disposable_database(container, env, database, evidence):
        with archive.open("rb") as source:
            execute(container, env, ["pg_restore", "--dbname", database, "--exit-on-error",
                                     "--no-owner", "--no-acl"], stdin=source)
        counts, columns, migrations, table_count = target_facts(container, env, database, facts[1])
        if (counts != facts[1] or columns != facts[2] or migrations != facts[3]
                or table_count != len(facts[1])):
            raise RestoreBlocked("restored_snapshot_integrity_mismatch")
        evidence.update(public_tables_verified=table_count, row_counts_match=True,
                        column_definitions_match=True, migration_history_match=True,
                        migration_records_verified=len(migrations))


@contextmanager
def private_archive(environ, evidence):
    with tempfile.TemporaryDirectory(prefix="crown-dev-backup-", dir=environ["RUNNER_TEMP"]) as directory:
        archive = Path(directory) / "private.dump"
        try:
            yield archive
        finally:
            archive.unlink(missing_ok=True)
            evidence["ephemeral_backup_removed"] = not archive.exists()


def perform(container, database, evidence, environ):
    import psycopg
    target_env = target_environment(environ)
    target_identity(container, target_env)  # Before reading DEV credentials or creating any DB.
    url, source_db = read_dev_database_setting()
    source_env = source_environment(url, source_db, environ)
    with private_archive(environ, evidence) as archive:
        with psycopg.connect(
            host=DEV_HOST, port=5432, dbname=source_db, user=source_env["PGUSER"],
            password=source_env["PGPASSWORD"], sslmode="verify-full", sslrootcert=CA,
            connect_timeout=12, options="-c default_transaction_read_only=on -c statement_timeout=300000",
        ) as connection:
            facts = read_snapshot(connection)
            evidence.update(source_snapshot_at_utc=facts[5], source_tls_verified=True,
                            source_transaction_read_only=True, source_postgres_version=facts[4])
            evidence["backup_started_at_utc"] = now()
            with archive.open("xb") as output:
                os.chmod(archive, 0o600)
                execute(container, source_env, ["pg_dump", "--format=custom", "--no-owner",
                        "--no-acl", "--lock-wait-timeout=10s", "--snapshot=" + facts[0]], stdout=output)
            connection.rollback()
        evidence["backup_completed_at_utc"] = now()
        evidence["backup_size_bytes"] = archive.stat().st_size
        if not evidence["backup_size_bytes"]:
            raise RestoreBlocked("backup_empty")
        digest = hashlib.sha256()
        with archive.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        evidence["backup_sha256"] = digest.hexdigest()
        with archive.open("rb") as source:
            execute(container, target_env, ["pg_restore", "--list"], stdin=source)
        restore_archive(container, target_env, database, archive, facts, evidence)
    if not evidence["ephemeral_backup_removed"]:
        raise RestoreBlocked("ephemeral_backup_cleanup_failed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--confirmation", required=True)
    parser.add_argument("--synthetic-dev-confirmed", required=True)
    parser.add_argument("--evidence-path", required=True)
    args = parser.parse_args(argv)
    started = time.monotonic()
    evidence = {
        "result": "BLOCKED", "started_at_utc": now(),
        "source_sha": args.expected_sha if re.fullmatch(r"[0-9a-f]{40}", args.expected_sha) else None,
        "source_app": DEV_APP, "source_database_identity_sha256": SOURCE_IDENTITY,
        "data_origin": "owner_attested_synthetic_dev" if args.synthetic_dev_confirmed == "true" else "NOT_VERIFIED",
        "source_write_performed": False,
        "disposable_database_created": False, "disposable_database_dropped": False,
        "application_rollback_compatibility": "NOT_TESTED", "release_readiness": "NOT_VERIFIED",
    }
    try:
        container, database = authority(args.expected_sha, args.confirmation,
                                        args.synthetic_dev_confirmed, os.environ)
        verify_accepted_source(args.expected_sha)
        perform(container, database, evidence, os.environ)
        evidence["result"] = "PASS"
    except Exception as exc:
        # Never expose PostgreSQL, Azure, URLs, row values, traceback or exception text.
        evidence["reason"] = str(exc) if isinstance(exc, RestoreBlocked) else "recovery_execution_blocked"
    evidence.update(completed_at_utc=now(), elapsed_seconds=round(time.monotonic() - started, 3))
    Path(args.evidence_path).write_text(json.dumps(evidence, indent=2) + "\n")
    print("DEV isolated restore: " + evidence["result"])
    return 0 if evidence["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
