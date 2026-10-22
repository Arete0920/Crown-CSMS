"""Read DEV blacklist migration metadata; never migrate, deploy, or print credentials.

Run only from an accepted-main checkout with the existing DEV GitHub environment.
The database connection is explicitly read-only, and only fixed SQL reads execute.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

from run_dev_inquiry_migration import (
    DEV_APP,
    DEV_HOST,
    read_azure,
    resolve_value,
    validate_database_url,
)

ROOT = Path(__file__).resolve().parents[2]
RESOURCE_GROUP = "crown-rg"
CA_FILE = Path("/etc/ssl/certs/ca-certificates.crt")
VENDOR_MIGRATIONS = (
    "0001_initial",
    "0002_outstandingtoken_jti_hex",
    "0003_auto_20171017_2007",
    "0004_auto_20171017_2013",
    "0005_remove_outstandingtoken_jti",
    "0006_auto_20171017_2113",
    "0007_auto_20171017_2214",
    "0008_migrate_to_bigautofield",
    "0010_fix_migrate_to_bigautofield",
    "0011_linearizes_history",
    "0012_alter_outstandingtoken_user",
    "0013_alter_blacklistedtoken_options_and_more",
)
COLUMNS = {
    "token_blacklist_outstandingtoken": {"id", "user_id", "jti", "token", "created_at", "expires_at"},
    "token_blacklist_blacklistedtoken": {"id", "token_id", "blacklisted_at"},
}
SETTING_FILTER = (
    "[?name=='CROWN_ENV' || name=='ENVIRONMENT' || name=='DJANGO_ENV' "
    "|| name=='DATABASE_URL'].{name:name,value:value}"
)


class EvidenceBlocked(RuntimeError):
    """Use fixed error codes so Azure, PostgreSQL and token details never leak."""


def verify_accepted_source(source_sha, *, runner=subprocess.run, root=ROOT):
    if not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise EvidenceBlocked("accepted_source_sha_required")
    try:
        head = runner(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True,
                      text=True, timeout=20, check=False)
        ancestor = runner(["git", "merge-base", "--is-ancestor", source_sha, "origin/main"],
                          cwd=root, capture_output=True, text=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EvidenceBlocked("accepted_source_unavailable") from exc
    if head.returncode or head.stdout.strip() != source_sha or ancestor.returncode:
        raise EvidenceBlocked("source_not_accepted_main_commit")


def read_dev_database_setting(*, read=read_azure):
    target = ["--resource-group", RESOURCE_GROUP, "--name", DEV_APP]
    app = read("webapp", "show", *target, "--query", "{name:name,defaultHostName:defaultHostName}")
    if not isinstance(app, dict) or app.get("name") != DEV_APP or app.get("defaultHostName") != DEV_APP + ".azurewebsites.net":
        raise EvidenceBlocked("dev_app_identity_not_verified")
    rows = read("webapp", "config", "appsettings", "list", *target, "--query", SETTING_FILTER)
    if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get("name"), str) for row in rows):
        raise EvidenceBlocked("dev_configuration_unavailable")
    values = {row["name"]: row.get("value") for row in rows}
    if len(values) != len(rows) or values.get("CROWN_ENV") != "dev" or values.get("ENVIRONMENT") != "dev" or values.get("DJANGO_ENV") != "development":
        raise EvidenceBlocked("dev_environment_markers_not_verified")
    database_url = resolve_value(values.get("DATABASE_URL"), read=read)
    return database_url, validate_database_url(database_url)


def classify_schema(names, tables, columns):
    names = set(names)
    expected = set(VENDOR_MIGRATIONS)
    if not names and not any(tables.values()):
        return "CLEAN_UNINITIALIZED"
    if names == expected and all(tables.values()) and all(columns.values()):
        return "VENDOR_HISTORY_AND_TABLES_PRESENT"
    return "RECONCILIATION_REQUIRED"


def inspect_database(database_url, database_name, *, connector=None, ca_file=CA_FILE):
    if validate_database_url(database_url) != database_name:
        raise EvidenceBlocked("database_target_not_verified_dev")
    if not ca_file.is_file():
        raise EvidenceBlocked("trusted_database_ca_unavailable")
    if connector is None:
        from psycopg import connect as connector

    # The options forbid writes even if a future statement is accidentally added.
    # A second transaction-level read-only check is performed before any SELECT.
    try:
        with connector(
            database_url,
            sslmode="verify-full",
            sslrootcert=str(ca_file),
            connect_timeout=12,
            autocommit=True,
            application_name="crown_blacklist_readonly_preflight",
            options="-c default_transaction_read_only=on -c statement_timeout=12000 -c lock_timeout=3000",
        ) as connection:
            with connection.transaction():
                with connection.cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                    cursor.execute("SHOW transaction_read_only")
                    if cursor.fetchone() != ("on",):
                        raise EvidenceBlocked("transaction_not_read_only")
                    cursor.execute("SELECT current_database(), current_schema(), pg_is_in_recovery()")
                    if cursor.fetchone() != (database_name, "public", False):
                        raise EvidenceBlocked("connected_database_identity_mismatch")
                    cursor.execute("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
                    if cursor.fetchone() != (True,):
                        raise EvidenceBlocked("database_tls_not_verified")
                    cursor.execute("SELECT name FROM django_migrations WHERE app = %s ORDER BY name", ("token_blacklist",))
                    names = [row[0] for row in cursor.fetchall()]
                    if any(not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_]{1,128}", name) for name in names):
                        raise EvidenceBlocked("unexpected_migration_identifier")
                    cursor.execute(
                        "SELECT to_regclass('public.token_blacklist_outstandingtoken') IS NOT NULL, "
                        "to_regclass('public.token_blacklist_blacklistedtoken') IS NOT NULL"
                    )
                    outstanding, blacklisted = cursor.fetchone()
                    cursor.execute(
                        "SELECT table_name, column_name FROM information_schema.columns "
                        "WHERE table_schema = 'public' AND table_name IN (%s, %s)",
                        tuple(COLUMNS),
                    )
                    actual = {key: set() for key in COLUMNS}
                    for table, column in cursor.fetchall():
                        if table in actual:
                            actual[table].add(column)
    except EvidenceBlocked:
        raise
    except Exception as exc:
        # The driver may include the connection string in exception text.
        raise EvidenceBlocked("database_metadata_read_unavailable") from exc

    tables = {"outstanding": bool(outstanding), "blacklisted": bool(blacklisted)}
    columns = {
        "outstanding": COLUMNS["token_blacklist_outstandingtoken"].issubset(actual["token_blacklist_outstandingtoken"]),
        "blacklisted": COLUMNS["token_blacklist_blacklistedtoken"].issubset(actual["token_blacklist_blacklistedtoken"]),
    }
    return {
        "database_identity_sha256": hashlib.sha256((DEV_HOST + "/" + database_name).encode()).hexdigest(),
        "tls_verified": True,
        "transaction_read_only_verified": True,
        "applied_blacklist_migrations": sorted(names),
        "blacklist_table_exists": tables,
        "expected_columns_present": columns,
        "schema_classification": classify_schema(names, tables, columns),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args(argv)
    packet = {
        "mode": "READ_ONLY", "status": "BLOCKED", "source_sha": args.expected_sha if re.fullmatch(r"[0-9a-f]{40}", args.expected_sha) else None,
        "target_app": DEV_APP, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "activation_authorized": False, "runtime_dependency_version": "NOT_VERIFIED",
        "deployed_build_identity": "NOT_VERIFIED",
    }
    stage = "source"
    try:
        verify_accepted_source(args.expected_sha)
        stage = "dev_configuration"
        database_url, name = read_dev_database_setting()
        stage = "database_read_only"
        packet.update(inspect_database(database_url, name))
        packet["status"] = "COLLECTED"
    except Exception as exc:
        packet["stage"] = stage
        packet["reason"] = str(exc) if isinstance(exc, EvidenceBlocked) else "evidence_collection_unavailable"
    print(json.dumps(packet, sort_keys=True))
    return 0 if packet["status"] == "COLLECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
