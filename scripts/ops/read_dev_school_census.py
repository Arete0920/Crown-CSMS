"""Read-only census of the original CROWN Azure DEV PostgreSQL school records.

The authenticated protected-main GitHub Actions job owns the invocation.
Never emit credentials, invitation IDs, names, full school UUIDs or personal data.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

from read_dev_blacklist_state import (
    CA_FILE, EvidenceBlocked, SAFE_CONFIGURATION_REASONS, RESOURCE_GROUP,
    read_dev_database_setting, verify_accepted_source,
)
from run_dev_inquiry_migration import Blocked, DEV_APP, DEV_HOST, read_azure, validate_database_url
from crown637_history_readonly import (
    AuditBlocked, requested_from_event, inspect_database as inspect_crown637_history,
)

HERITAGE_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"
HERITAGE_NAME = "Heritage Christian Academy"
BUYER_NAME = "Heritage Christian Academy - Fictional Buyer Workspace"
MAX_SCHOOLS = 1000

DEMO_FLAG_NAMES = (
    "CROWN_SANDBOX_ALLOW_OPEN_SESSION",
    "CROWN_HOSTED_JIREH_DEMO_ENABLED",
)
DEMO_FLAG_FILTER = (
    "[?name=='CROWN_SANDBOX_ALLOW_OPEN_SESSION' || "
    "name=='CROWN_HOSTED_JIREH_DEMO_ENABLED'].{name:name,value:value}"
)


def read_demo_flag_markers(*, read=read_azure):
    """Read only two DEV App Service markers; never emit secrets or raw errors.

    The caller verifies the exact Azure DEV app identity first. A value is
    confirmed only when it is a literal boolean; absent, duplicate, Key Vault
    reference or unexpected values are UNVERIFIED, not guessed false.
    """
    result = {key: "UNVERIFIED" for key in DEMO_FLAG_NAMES}
    try:
        rows = read(
            "webapp", "config", "appsettings", "list",
            "--resource-group", RESOURCE_GROUP, "--name", DEV_APP,
            "--query", DEMO_FLAG_FILTER,
        )
    except Exception:
        return result
    if not isinstance(rows, list):
        return result
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            return {key: "UNVERIFIED" for key in DEMO_FLAG_NAMES}
        key = row.get("name")
        if key not in result:
            continue
        if key in seen:
            result[key] = "UNVERIFIED"
            continue
        seen.add(key)
        raw = row.get("value")
        if isinstance(raw, str) and raw.strip().lower() in ("true", "false"):
            result[key] = raw.strip().lower()
    return result


# Explicit table/model identity: core Family/Student != portal Household/Student.
# Query is fixed and schema-qualified; no untrusted value is interpolated.
CENSUS_SQL = """
SELECT s.id::text, s.name, w.source_sha,
       (SELECT count(*) FROM public.core_family AS f WHERE f.school_id = s.id),
       (SELECT count(*) FROM public.core_student AS x WHERE x.school_id = s.id),
       (SELECT count(*) FROM public.household AS h WHERE h.school_id = s.id),
       (SELECT count(*) FROM public.student AS p WHERE p.school_id = s.id)
FROM public.core_school AS s
LEFT JOIN public.sandbox_demo_sandboxbuyerworkspace AS w ON w.school_id = s.id
ORDER BY s.id
""".strip()


class CensusBlocked(RuntimeError):
    """Only fixed, non-sensitive reason codes leave this module."""


def classify(school_id, school_name, buyer_source):
    if buyer_source is not None:
        return "invite_owned_buyer"
    if school_id == HERITAGE_ID and school_name == HERITAGE_NAME:
        return "canonical_heritage"
    if school_name == HERITAGE_NAME:
        return "heritage_name_different_id"
    if school_name == BUYER_NAME:
        return "buyer_name_without_workspace"
    return "other"


def format_rows(rows, expected_sha):
    if len(rows) > MAX_SCHOOLS:
        raise CensusBlocked("school_inventory_limit_exceeded")
    result = []
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != 7:
            raise CensusBlocked("unexpected_school_inventory_shape")
        school_id, school_name, buyer_source, *values = row
        if (
            not isinstance(school_id, str)
            or re.fullmatch(r"[0-9a-f-]{36}", school_id) is None
            or not isinstance(school_name, str)
            or (buyer_source is not None and (
                not isinstance(buyer_source, str)
                or re.fullmatch(r"[0-9a-f]{40}", buyer_source) is None))
            or any(type(count) is not int or count < 0 for count in values)
        ):
            raise CensusBlocked("unexpected_school_inventory_values")
        result.append({
            "school_ref_sha256_16": hashlib.sha256(school_id.encode("ascii")).hexdigest()[:16],
            "classification": classify(school_id, school_name, buyer_source),
            "buyer_workspace_exact_source": (buyer_source == expected_sha if buyer_source is not None else None),
            "core_families": values[0],
            "core_students": values[1],
            "portal_households": values[2],
            "portal_students": values[3],
        })
    count_keys = ("core_families", "core_students", "portal_households", "portal_students")
    return {
        "school_count": len(result),
        "buyer_workspace_count": sum(row["classification"] == "invite_owned_buyer" for row in result),
        "totals": {key: sum(row[key] for row in result) for key in count_keys},
        "schools": result,
    }


def inspect_database(database_url, database_name, expected_sha, *, connector=None, ca_file=CA_FILE):
    if validate_database_url(database_url) != database_name:
        raise CensusBlocked("database_target_not_verified_dev")
    if not Path(ca_file).is_file():
        raise CensusBlocked("trusted_database_ca_unavailable")
    if connector is None:
        from psycopg import connect as connector
    try:
        with connector(
            database_url, sslmode="verify-full", sslrootcert=str(ca_file), connect_timeout=12,
            autocommit=True, application_name="crown_dev_school_census_readonly",
            options="-c default_transaction_read_only=on -c statement_timeout=12000 -c lock_timeout=3000",
        ) as conn:
            with conn.transaction():
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                    cursor.execute("SHOW transaction_read_only")
                    if cursor.fetchone() != ("on",):
                        raise CensusBlocked("transaction_not_read_only")
                    cursor.execute("SELECT current_database(), current_schema(), pg_is_in_recovery()")
                    if cursor.fetchone() != (database_name, "public", False):
                        raise CensusBlocked("connected_database_identity_mismatch")
                    cursor.execute("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
                    if cursor.fetchone() != (True,):
                        raise CensusBlocked("database_tls_not_verified")
                    cursor.execute(CENSUS_SQL)
                    rows = cursor.fetchall()
        return {
            "database_identity_sha256": hashlib.sha256((DEV_HOST + "/" + database_name).encode()).hexdigest(),
            "tls_verified": True,
            "transaction_read_only_verified": True,
            **format_rows(rows, expected_sha),
        }
    except CensusBlocked:
        raise
    except Exception as exc:
        # psycopg exceptions sometimes contain connection strings.
        raise CensusBlocked("database_census_read_unavailable") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    args = parser.parse_args(argv)
    sha = args.expected_sha if re.fullmatch(r"[0-9a-f]{40}", args.expected_sha) else None
    packet = {
        "mode": "READ_ONLY", "status": "BLOCKED", "source_sha": sha,
        "target_app": DEV_APP, "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "database_writes_authorized": False, "buyer_certified": False,
    }
    stage = "source"
    try:
        verify_accepted_source(args.expected_sha)
        stage = "requested_operation"
        crown637_mode = requested_from_event()
        stage = "dev_configuration"
        database_url, name = read_dev_database_setting()
        packet["dev_demo_appsettings"] = read_demo_flag_markers()
        stage = "database_read_only"
        packet.update(inspect_database(database_url, name, args.expected_sha))
        if crown637_mode:
            # Separate guarded manual read; normal DEV inventory is unchanged.
            stage = "historical_integrity"
            from psycopg import connect
            packet["crown637_history"] = inspect_crown637_history(
                database_url, name, args.expected_sha,
                validate_database_url=validate_database_url, dev_host=DEV_HOST,
                ca_file=CA_FILE, connector=connect,
            )
            if packet["crown637_history"]["school_count"] != packet["school_count"]:
                raise AuditBlocked("historical_school_coverage_mismatch")
        packet["status"] = "COLLECTED"
    except Exception as exc:
        reason = str(exc)
        packet["stage"] = stage
        packet["reason"] = (reason if (
            (isinstance(exc, (CensusBlocked, EvidenceBlocked, AuditBlocked))
             and re.fullmatch(r"[a-z_]{3,80}", reason))
            or (isinstance(exc, Blocked) and reason in SAFE_CONFIGURATION_REASONS)
        ) else "census_evidence_unavailable")
    print(json.dumps(packet, sort_keys=True))
    return 0 if packet["status"] == "COLLECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
