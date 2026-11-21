#!/usr/bin/env python3
"""CROWN #637: aggregate, read-only historical enrollment/identity risk screen.

Run only inside the authorized protected-main DEV OIDC inventory context.
This screen reports candidates, NOT proven corrupt records or closure clearance.
No names, birth dates, application/student IDs or raw database errors are emitted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re

METRICS = (
    "legacy_app_number_candidates",
    "legacy_app_number_near_creation_dob_candidates",
    "legacy_app_number_without_verified_identity",
    "canonical_marked_legacy_without_verified_identity",
    "verified_admissions_provenance_unmatched",
    "invalid_identity_link_scope_or_evidence",
    "enrolled_legacy_without_matching_core_enrollment",
    "duplicate_legacy_enrollment_keys_excess_rows",
)
MAX_SCHOOLS = 1000
MANUAL_MARKER = "crown637-history-readonly"


def requested_from_event(environ=None):
    """Require an explicit, unambiguous manual read-only dispatch.

    The canonical DEV inventory workflow already exposes confirm_dev_support as
    an optional string input. This unique marker cannot activate any migration
    stage. A protected-main exact-SHA check still runs in the workflow itself.
    Ordinary push/PR/manual inventory and the #269 metadata mode remain inert.
    """
    env = os.environ if environ is None else environ
    if env.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        return False
    event_path = env.get("GITHUB_EVENT_PATH")
    if not event_path:
        return False
    try:
        path = Path(event_path)
        if not path.is_file() or path.stat().st_size > 65536:
            raise AuditBlocked("history_event_unavailable")
        event = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise AuditBlocked("history_event_unavailable") from exc
    inputs = event.get("inputs") if isinstance(event, dict) else None
    if not isinstance(inputs, dict) or inputs.get("confirm_dev_support") != MANUAL_MARKER:
        return False
    sha = inputs.get("expected_sha")
    if (env.get("GITHUB_REPOSITORY") != "Arete0920/Crown-CSMS"
            or env.get("GITHUB_REF") != "refs/heads/main"
            or not isinstance(sha, str)
            or not re.fullmatch(r"[0-9a-f]{40}", sha)
            or sha != env.get("GITHUB_SHA")):
        raise AuditBlocked("history_source_or_repo_mismatch")
    for flag in ("compare_rehearsal_baseline", "inspect_migration_plan",
                 "apply_reviewed_support", "apply_reviewed_legacy_refresh",
                 "apply_reviewed_blacklist"):
        if inputs.get(flag) not in (None, False, "", "false"):
            raise AuditBlocked("history_mixed_mutation_or_diagnostic_modes")
    for key in ("confirm_dev_legacy_refresh", "confirm_dev_blacklist",
                "dev_recovery_receipt"):
        if inputs.get(key) not in (None, ""):
            raise AuditBlocked("history_mixed_confirmation")
    return True

# Fixed-source, fixed-table query. All joins/filters are tenant-scoped. No raw rows
# or PII leave the database; DOB is only tested as a broad candidate signal.
READ_ONLY_SQL = """
SELECT s.id::text,
  (SELECT COUNT(*) FROM public.core_student c
   WHERE c.school_id=s.id AND c.student_number ~ '^APP-[0-9a-f]{6}-[0-9]{2,}$'),
  (SELECT COUNT(*) FROM public.core_student c
   WHERE c.school_id=s.id AND c.student_number ~ '^APP-[0-9a-f]{6}-[0-9]{2,}$'
     AND c.dob BETWEEN (c.created_at AT TIME ZONE 'UTC')::date - 1
                   AND (c.created_at AT TIME ZONE 'UTC')::date + 1),
  (SELECT COUNT(*) FROM public.core_student c
   WHERE c.school_id=s.id AND c.student_number ~ '^APP-[0-9a-f]{6}-[0-9]{2,}$'
     AND NOT EXISTS (
       SELECT 1 FROM public.core_studentidentitylink l
       WHERE l.school_id=s.id AND l.core_student_id=c.id
         AND l.verification_status='verified' AND BTRIM(l.evidence_reference)<>'')),
  -- The historical bridge could also reuse an unrelated same-name core
  -- student, not only create an APP-numbered one. Inspect canonical-marked
  -- legacy records regardless of student-number pattern.
  (SELECT COUNT(*) FROM public.admissions_admissionsapplication a
   WHERE a.school_id=s.id AND a.student_id IS NOT NULL
     AND a.notes_internal LIKE '%canonical_application_id=%'
     AND NOT EXISTS (
       SELECT 1 FROM public.core_studentidentitylink l
       WHERE l.school_id=s.id AND l.core_student_id=a.student_id
         AND l.source='admissions' AND l.verification_status='verified'
         AND BTRIM(l.evidence_reference)<>'')),
  (SELECT COUNT(*) FROM public.core_studentidentitylink l
   JOIN public.core_student c ON c.id=l.core_student_id
   JOIN public.student p ON p.id=l.compatibility_student_id
   WHERE l.school_id=s.id AND l.source='admissions'
     AND l.verification_status='verified'
     AND NOT EXISTS (
       SELECT 1 FROM public.applicant x
       JOIN public.application a ON a.id=x.application_id
       WHERE x.school_id=s.id AND a.school_id=s.id
         AND x.student_id=l.compatibility_student_id
         AND a.household_id=p.household_id AND x.dob=c.dob
         AND l.evidence_reference='application:'||a.id::text||':applicant:'||x.id::text)),
  (SELECT COUNT(*) FROM public.core_studentidentitylink l
   JOIN public.core_student c ON c.id=l.core_student_id
   JOIN public.student p ON p.id=l.compatibility_student_id
   WHERE l.school_id=s.id AND (
     c.school_id<>s.id OR p.school_id<>s.id
     OR (l.verification_status='verified' AND BTRIM(l.evidence_reference)=''))),
  (SELECT COUNT(*) FROM public.admissions_admissionsapplication a
   WHERE a.school_id=s.id AND a.status='ENROLLED'
     AND (a.student_id IS NULL OR NOT EXISTS (
       SELECT 1 FROM public.core_enrollment e
       WHERE e.school_id=a.school_id AND e.student_id=a.student_id
         AND e.academic_year_id=a.academic_year_id))),
  (SELECT COALESCE(SUM(d.n-1), 0)::bigint FROM (
     SELECT COUNT(*) AS n FROM public.admissions_admissionsapplication a
     WHERE a.school_id=s.id AND a.student_id IS NOT NULL
     GROUP BY a.school_id, a.academic_year_id, a.family_id, a.student_id
     HAVING COUNT(*) > 1
   ) d)
FROM public.core_school s
ORDER BY s.id
""".strip()


class AuditBlocked(RuntimeError):
    """Error category intentionally contains no source database content."""


def format_counts(rows):
    if not isinstance(rows, (list, tuple)) or not rows or len(rows) > MAX_SCHOOLS:
        raise AuditBlocked("unexpected_school_coverage")
    expected = 1 + len(METRICS)
    seen = set()
    totals = {key: 0 for key in METRICS}
    schools_affected = {key: 0 for key in METRICS}
    for row in rows:
        if not isinstance(row, (tuple, list)) or len(row) != expected:
            raise AuditBlocked("unexpected_audit_result")
        school_id = row[0]
        if not isinstance(school_id, str) or not re.fullmatch(r"[0-9a-f-]{36}", school_id) or school_id in seen:
            raise AuditBlocked("unexpected_school_coverage")
        seen.add(school_id)
        for key, count in zip(METRICS, row[1:]):
            if type(count) is not int or count < 0:
                raise AuditBlocked("unexpected_audit_count")
            totals[key] += count
            schools_affected[key] += int(count > 0)
    return {
        "school_count": len(seen),
        "aggregate_candidate_counts": totals,
        "schools_with_candidates": schools_affected,
        "interpretation": "SCREEN_ONLY_NOT_PROOF_OF_HISTORICAL_CORRUPTION_OR_CLEARANCE",
        "privacy": "NO_STUDENT_SCHOOL_IDENTIFIERS_NAMES_DATES_OR_RAW_ROWS",
    }


def inspect_database(database_url, database_name, expected_sha, *,
                     validate_database_url, dev_host, ca_file, connector):
    if not isinstance(expected_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise AuditBlocked("invalid_source_sha")
    if validate_database_url(database_url) != database_name:
        raise AuditBlocked("wrong_dev_database_target")
    if not Path(ca_file).is_file():
        raise AuditBlocked("trusted_ca_unavailable")
    with connector(
        database_url,
        sslmode="verify-full",
        sslrootcert=str(ca_file),
        connect_timeout=12,
        autocommit=True,
        application_name="crown637_history_readonly",
        options="-c default_transaction_read_only=on -c statement_timeout=12000 -c lock_timeout=3000",
    ) as conn:
        with conn.transaction():
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                cursor.execute("SHOW transaction_read_only")
                if cursor.fetchone() != ("on",):
                    raise AuditBlocked("database_transaction_not_read_only")
                cursor.execute("SELECT current_database(), current_schema(), pg_is_in_recovery()")
                if cursor.fetchone() != (database_name, "public", False):
                    raise AuditBlocked("database_identity_mismatch")
                cursor.execute("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
                if cursor.fetchone() != (True,):
                    raise AuditBlocked("database_tls_not_verified")
                cursor.execute(READ_ONLY_SQL)
                report = format_counts(cursor.fetchall())
    return {
        "source_sha": expected_sha,
        "dev_database_target_verified": True,
        "transaction_read_only_verified": True,
        "tls_verified": True,
        "database_writes": "NONE",
        **report,
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--expected-sha", required=True)
    args = p.parse_args(argv)
    result = {
        "issue": 637,
        "mode": "READ_ONLY_SCREEN",
        "status": "BLOCKED",
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha": args.expected_sha if re.fullmatch(r"[0-9a-f]{40}", args.expected_sha) else "NOT_VERIFIED",
        "database_writes_authorized": False,
    }
    try:
        from read_dev_school_census import (
            CA_FILE, DEV_HOST, read_dev_database_setting,
            validate_database_url, verify_accepted_source,
        )
        from psycopg import connect
        verify_accepted_source(args.expected_sha)
        database_url, database_name = read_dev_database_setting()
        result.update(inspect_database(
            database_url, database_name, args.expected_sha,
            validate_database_url=validate_database_url, dev_host=DEV_HOST,
            ca_file=CA_FILE, connector=connect,
        ))
        result["status"] = "COLLECTED_SCREEN_ONLY"
    except Exception:
        # Never serialize exception strings: they can include DB URLs and secrets.
        result["reason"] = "read_only_history_evidence_unavailable"
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "COLLECTED_SCREEN_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
