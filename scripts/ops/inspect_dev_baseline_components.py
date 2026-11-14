"""Read-only, fixed-category DEV baseline comparison for issue #427.

Never emit source rows, connection strings, table names, or raw fingerprints.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "ops"))
from run_dev_inquiry_migration import load_dev_settings, validate_database_url, DEV_HOST
from rehearse_dev_heritage_migrations import (
    table_facts, row_digest, data_fingerprint, component_fingerprint,
)

def inspect(expected_sha, baseline_columns, baseline_rows, baseline_combined):
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise ValueError("invalid_exact_sha")
    if any(not re.fullmatch(r"[0-9a-f]{64}", v)
           for v in (baseline_columns, baseline_rows, baseline_combined)):
        raise ValueError("invalid_rehearsal_fingerprint")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() != expected_sha:
        raise ValueError("source_sha_mismatch")
    subprocess.run(["git", "fetch", "--no-tags", "origin", "refs/heads/main:refs/remotes/origin/main"],
                   cwd=ROOT, check=True, capture_output=True)
    if subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip() != expected_sha:
        raise ValueError("protected_main_moved")
    url, secret, db_name, blacklist = load_dev_settings()
    if blacklist or validate_database_url(url) != db_name:
        raise ValueError("dev_database_boundary_failed")
    ca = Path("/etc/ssl/certs/ca-certificates.crt")
    if not ca.is_file():
        raise ValueError("trusted_ca_missing")
    tls_url = urlsplit(url)._replace(query=urlencode({
        "sslmode": "verify-full", "sslrootcert": str(ca), "connect_timeout": 12,
    })).geturl()
    os.environ.update(
        DATABASE_URL=tls_url, DJANGO_SECRET_KEY=secret,
        DJANGO_SETTINGS_MODULE="crown_api.settings", CROWN_ENV="dev",
        DJANGO_ENV="development", ENVIRONMENT="dev",
        DEBUG="false", DJANGO_DEBUG="false",
        CROWN_SIMPLEJWT_BLACKLIST_ENABLED="false", CROWN_DEMO_MODE="false",
        BUILD_SHA=expected_sha,
    )
    sys.path.insert(0, str(ROOT / "backend"))
    import django
    django.setup()
    from django.db import connection, transaction
    if (connection.vendor != "postgresql"
            or connection.settings_dict["HOST"] != DEV_HOST
            or connection.settings_dict["NAME"] != db_name):
        raise ValueError("live_dev_identity_failed")
    connection.settings_dict["OPTIONS"] = {
        "sslmode": "verify-full", "sslrootcert": str(ca), "connect_timeout": 12,
    }
    connection.close()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute("SET LOCAL statement_timeout = '180s'")
            cursor.execute("SELECT current_database(), current_schema(), pg_is_in_recovery(), current_setting('server_version_num')::integer")
            db, schema, recovery, version = cursor.fetchone()
            if (db, schema, recovery) != (db_name, "public", False) or version // 10000 != 15:
                raise ValueError("postgres_target_failed")
            cursor.execute("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
            if cursor.fetchone() != (True,):
                raise ValueError("tls_not_verified")
            cursor.execute("SHOW transaction_read_only")
            if cursor.fetchone() != ("on",):
                raise ValueError("read_only_not_verified")
        columns = table_facts(connection)
        rows = {table: row_digest(connection, table, names) for table, names in columns.items()}
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM public.django_migrations")
            migration_records = cursor.fetchone()[0]
    col_diff = component_fingerprint(columns) != baseline_columns
    row_diff = component_fingerprint(rows) != baseline_rows
    combined_diff = data_fingerprint(columns, rows) != baseline_combined
    category = ("columns_and_rows" if col_diff and row_diff else
                "columns" if col_diff else "rows" if row_diff else
                "combined_only" if combined_diff else "match")
    return {
        "result": "MATCH" if category == "match" and migration_records == 245 and len(columns) == 467 else "DIFF",
        "category": category,
        "migration_records_match": migration_records == 245,
        "public_tables_match": len(columns) == 467,
        "source_sha": expected_sha,
        "read_only": True,
        "live_schema_write_performed": False,
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--expected-sha", required=True)
    p.add_argument("--columns", required=True)
    p.add_argument("--rows", required=True)
    p.add_argument("--combined", required=True)
    a = p.parse_args()
    try:
        result = inspect(a.expected_sha, a.columns, a.rows, a.combined)
    except Exception:
        result = {"result": "BLOCKED", "reason": "read_only_baseline_inspection_failed",
                  "read_only": True, "live_schema_write_performed": False}
    finally:
        for key in ("DATABASE_URL", "DJANGO_SECRET_KEY"):
            os.environ.pop(key, None)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["result"] != "BLOCKED" else 1

if __name__ == "__main__":
    raise SystemExit(main())
