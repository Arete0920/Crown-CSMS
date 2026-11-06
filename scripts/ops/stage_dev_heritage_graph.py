"""Fail-closed DEV-only reviewed 21-migration stage for issue #427.

Never called by ordinary deploy-dev. Cannot self-authorize; GitHub Actions dev
workflow owns consent, provenance and maintenance window. Does not create Azure
resources, activate feature flags, provision schools or touch production.
"""
from __future__ import annotations

import argparse
from contextlib import redirect_stdout, redirect_stderr
from io import BytesIO
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlencode, urlsplit
from urllib.error import HTTPError
from urllib.request import Request, HTTPRedirectHandler, build_opener, urlopen
from zipfile import BadZipFile, ZipFile

ROOT = Path(__file__).resolve().parents[2]
DEV_APP = 'crown-api-dev'
EXPECTED_COUNT = 21
CONFIRMATION = 'migrate-dev-reviewed-21'
REPO = 'Arete0920/Crown-CSMS'
REPO_ID = 1339719218
REHEARSAL_WORKFLOW = '.github/workflows/isolated-postgres-restore-drill.yml'
REHEARSAL_RECEIPT_NAME = 'dev-restore-evidence.json'
MAX_EVIDENCE_ZIP = 64 * 1024

class StageBlocked(RuntimeError):
    """Only a fixed non-sensitive reason code is exported."""


def _allowed_sha(value):
    return isinstance(value, str) and re.fullmatch(r'[0-9a-f]{40}', value) is not None


def authority(expected_sha, confirmation, synthetic, backup, maintenance, run_id, environ):
    """All authorizations must be explicit before configuration/secret reads."""
    if not _allowed_sha(expected_sha):
        raise StageBlocked('exact_source_sha_required')
    if (environ.get('GITHUB_ACTIONS') != 'true'
            or environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch'
            or environ.get('GITHUB_REF') != 'refs/heads/main'
            or environ.get('GITHUB_SHA') != expected_sha):
        raise StageBlocked('manual_protected_main_only')
    if (confirmation != CONFIRMATION or synthetic != 'true' or backup != 'true'
            or maintenance != 'true'):
        raise StageBlocked('owner_approval_or_recovery_evidence_missing')
    stage_run = environ.get('GITHUB_RUN_ID', '')
    if (not isinstance(run_id, str) or not re.fullmatch(r'[1-9][0-9]{5,19}', run_id)
            or not isinstance(stage_run, str) or not re.fullmatch(r'[1-9][0-9]{5,19}', stage_run)
            or int(run_id) >= int(stage_run)):
        # The prior RESTORED-COPY run and this future SCHEMA-STAGE run are distinct.
        raise StageBlocked('prior_reviewed_rehearsal_run_id_required')
    if (environ.get('GITHUB_REPOSITORY') != REPO
            or environ.get('GITHUB_REPOSITORY_ID') != str(REPO_ID)):
        raise StageBlocked('trusted_repository_identity_required')
    return int(run_id)


def receipt_contract(receipt, expected_sha):
    """Rehearsal evidence only; does not substitute for checking live DB plan."""
    if not isinstance(receipt, dict) or not _allowed_sha(expected_sha):
        raise StageBlocked('reviewed_restore_receipt_invalid')
    rehearsal = receipt.get('migration_rehearsal')
    required_outer = {
        'result': 'PASS', 'source_sha': expected_sha,
        'source_app': DEV_APP, 'data_origin': 'owner_attested_synthetic_dev',
        'source_write_performed': False, 'source_tls_verified': True,
        'source_transaction_read_only': True,
        'disposable_database_created': True, 'disposable_database_dropped': True,
        'ephemeral_backup_removed': True, 'migration_rehearsal_requested': True,
        'application_rollback_compatibility': 'NOT_TESTED',
    }
    required_inner = {
        'result': 'PASS', 'source_sha': expected_sha,
        'target_postgres_major': 15, 'reviewed_migrations': EXPECTED_COUNT,
        'remaining_pending': 0, 'existing_seed_rows_preserved': True,
        'existing_nonseed_table_values_preserved': True,
        'existing_table_counts_preserved': True, 'atomic_graph': True,
        'legacy_inserts_preserved': True, 'live_schema_write_performed': False,
    }
    if (not isinstance(rehearsal, dict)
            or any(type(receipt.get(k)) is not type(v) or receipt.get(k) != v
                   for k, v in required_outer.items())
            or any(type(rehearsal.get(k)) is not type(v) or rehearsal.get(k) != v
                   for k, v in required_inner.items())
            or type(rehearsal.get('baseline_migration_records')) is not int
            or rehearsal['baseline_migration_records'] < 1
            or type(rehearsal.get('migrated_records')) is not int
            or rehearsal['migrated_records'] != rehearsal['baseline_migration_records'] + EXPECTED_COUNT
            or type(rehearsal.get('baseline_public_tables')) is not int
            or rehearsal['baseline_public_tables'] < 1
            or receipt.get('row_counts_match') is not True
            or receipt.get('column_definitions_match') is not True
            or receipt.get('migration_history_match') is not True
            or type(receipt.get('backup_size_bytes')) is not int
            or receipt.get('backup_size_bytes', 0) < 1
            or not isinstance(receipt.get('backup_sha256'), str)
            or re.fullmatch(r'[0-9a-f]{64}', receipt['backup_sha256']) is None
            or not isinstance(receipt.get('source_database_identity_sha256'), str)
            or re.fullmatch(r'[0-9a-f]{64}', receipt['source_database_identity_sha256']) is None
            or not isinstance(rehearsal.get('baseline_fingerprint'), str)
            or re.fullmatch(r'[0-9a-f]{64}', rehearsal['baseline_fingerprint']) is None):
        raise StageBlocked('reviewed_restore_receipt_invalid')
    if type(receipt.get('source_postgres_version')) is not int or receipt['source_postgres_version'] // 10000 != 15:
        raise StageBlocked('source_postgresql15_not_verified')
    return True



def _github_api_json(path, token):
    """Read GitHub Actions evidence using a repository-scoped Actions read token."""
    request = Request(
        f'https://api.github.com/repos/{REPO}/actions/{path}',
        headers={'Accept': 'application/vnd.github+json',
                 'Authorization': 'Bearer ' + token,
                 'X-GitHub-Api-Version': '2022-11-28',
                 'User-Agent': 'CROWN-DEV-427-review'},
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(256 * 1024 + 1)
        if len(body) > 256 * 1024:
            raise StageBlocked('rehearsal_github_metadata_too_large')
        return json.loads(body)
    except StageBlocked:
        raise
    except Exception:
        raise StageBlocked('rehearsal_github_metadata_unverified') from None


class _NoRedirect(HTTPRedirectHandler):
    """Never forward the GitHub token to a storage-service redirect."""

    def redirect_request(self, request, fp, code, message, headers, new_url):
        return None


def _fetch_artifact_zip(artifact_id, token):
    request = Request(
        f'https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip',
        headers={'Accept': 'application/vnd.github+json',
                 'Authorization': 'Bearer ' + token,
                 'User-Agent': 'CROWN-DEV-427-review'},
    )
    try:
        with build_opener(_NoRedirect()).open(request, timeout=20):
            raise StageBlocked('rehearsal_artifact_redirect_required')
    except HTTPError as error:
        if error.code != 302:
            raise StageBlocked('rehearsal_artifact_download_denied') from None
        location = error.headers.get('Location', '')
    except StageBlocked:
        raise
    except Exception:
        raise StageBlocked('rehearsal_artifact_download_denied') from None

    target = urlsplit(location)
    host = (target.hostname or '').lower()
    if (target.scheme != 'https' or not host
            or not (host.endswith('.blob.core.windows.net')
                    or host.endswith('.githubusercontent.com'))
            or target.username or target.password):
        raise StageBlocked('rehearsal_artifact_storage_origin_denied')
    # This second request intentionally carries NO Authorization header.
    try:
        with urlopen(Request(location, headers={'User-Agent': 'CROWN-DEV-427-review'}),
                     timeout=30) as response:
            final = urlsplit(response.geturl())
            if final.scheme != 'https' or (final.hostname or '').lower() != host:
                raise StageBlocked('rehearsal_artifact_storage_origin_denied')
            body = response.read(MAX_EVIDENCE_ZIP + 1)
        if len(body) > MAX_EVIDENCE_ZIP:
            raise StageBlocked('rehearsal_artifact_too_large')
        return body
    except StageBlocked:
        raise
    except Exception:
        raise StageBlocked('rehearsal_artifact_download_denied') from None


def authenticated_rehearsal_receipt(run_id, artifact_id, expected_sha, environ):
    """Bind a prior successful restore to GitHub run, ZIP digest and receipt.

    The schema-stage run must have its own GITHUB_RUN_ID. A local JSON path or
    operator-provided checksum alone never establishes the prior run's identity.
    """
    token = environ.get('CROWN_STAGE_GITHUB_TOKEN', '')
    if (not isinstance(token, str) or not token or any(ord(ch) <= 32 for ch in token)
            or not isinstance(artifact_id, str)
            or not re.fullmatch(r'[1-9][0-9]{5,19}', run_id)
            or not re.fullmatch(r'[1-9][0-9]{5,19}', artifact_id)):
        raise StageBlocked('authenticated_rehearsal_artifact_required')
    run = _github_api_json(f'runs/{run_id}', token)
    if (not isinstance(run, dict)
            or type(run.get('id')) is not int or run['id'] != int(run_id)
            or run.get('status') != 'completed' or run.get('conclusion') != 'success'
            or run.get('event') != 'workflow_dispatch'
            or run.get('head_branch') != 'main' or run.get('head_sha') != expected_sha
            or not isinstance(run.get('path'), str)
            or run['path'].split('@')[0] != REHEARSAL_WORKFLOW
            or not isinstance(run.get('repository'), dict)
            or run['repository'].get('id') != REPO_ID
            or run['repository'].get('full_name') != REPO
            or not isinstance(run.get('head_repository'), dict)
            or run['head_repository'].get('id') != REPO_ID):
        raise StageBlocked('rehearsal_workflow_identity_unverified')
    listing = _github_api_json(f'runs/{run_id}/artifacts?per_page=100', token)
    if (not isinstance(listing, dict) or type(listing.get('total_count')) is not int
            or not isinstance(listing.get('artifacts'), list)
            or listing['total_count'] != len(listing['artifacts'])):
        raise StageBlocked('rehearsal_artifact_inventory_unverified')
    matches = [item for item in listing['artifacts']
               if isinstance(item, dict)
               and item.get('name') == 'dev-operational-restore-' + run_id]
    if len(matches) != 1:
        raise StageBlocked('rehearsal_artifact_ambiguous')
    artifact = matches[0]
    provenance = artifact.get('workflow_run')
    digest = artifact.get('digest')
    if (type(artifact.get('id')) is not int or artifact['id'] != int(artifact_id)
            or artifact.get('expired') is not False
            or type(artifact.get('size_in_bytes')) is not int
            or not 0 < artifact['size_in_bytes'] <= MAX_EVIDENCE_ZIP
            or not isinstance(digest, str)
            or not re.fullmatch(r'sha256:[0-9a-f]{64}', digest)
            or not isinstance(provenance, dict)
            or provenance.get('id') != int(run_id)
            or provenance.get('repository_id') != REPO_ID
            or provenance.get('head_repository_id') != REPO_ID
            or provenance.get('head_branch') != 'main'
            or provenance.get('head_sha') != expected_sha):
        raise StageBlocked('rehearsal_artifact_metadata_unverified')
    archive = _fetch_artifact_zip(artifact_id, token)
    if hashlib.sha256(archive).hexdigest() != digest.split(':', 1)[1]:
        raise StageBlocked('rehearsal_artifact_digest_mismatch')
    try:
        with ZipFile(BytesIO(archive)) as z:
            entries = z.infolist()
            if (len(entries) != 1 or entries[0].filename != REHEARSAL_RECEIPT_NAME
                    or entries[0].is_dir() or entries[0].file_size > 16 * 1024):
                raise StageBlocked('rehearsal_receipt_archive_invalid')
            receipt = json.loads(z.read(entries[0]))
    except StageBlocked:
        raise
    except (BadZipFile, ValueError, UnicodeError, OSError):
        raise StageBlocked('rehearsal_receipt_archive_invalid') from None
    receipt_contract(receipt, expected_sha)
    return receipt


def live_baseline_contract(receipt, fingerprint, migration_records, public_tables):
    """Refuse a stale restored-copy rehearsal before any live schema mutation.

    The fingerprint hashes the original public columns and row digests, using
    the same data_fingerprint() implementation as the disposable PG15 drill.
    A matching DB hostname alone cannot establish the same data baseline.
    """
    rehearsal = receipt.get('migration_rehearsal') if isinstance(receipt, dict) else None
    if (
        not isinstance(rehearsal, dict)
        or not isinstance(fingerprint, str)
        or re.fullmatch(r'[0-9a-f]{64}', fingerprint) is None
        or type(migration_records) is not int
        or type(public_tables) is not int
        or fingerprint != rehearsal.get('baseline_fingerprint')
        or migration_records != rehearsal.get('baseline_migration_records')
        or public_tables != rehearsal.get('baseline_public_tables')
    ):
        raise StageBlocked('live_dev_baseline_differs_from_rehearsal')
    return True


def plan_contract(plan, reviewed):
    """Accept precisely the reviewed non-reverse DAG, never a partial suffix."""
    if not isinstance(plan, list) or len(plan) != EXPECTED_COUNT:
        raise StageBlocked('live_pending_graph_differs_from_rehearsal')
    observed = []
    for item, reverse in plan:
        identity = f'{item.app_label}.{item.name}'
        if (reverse or not re.fullmatch(r'[a-z0-9_]+\.[a-zA-Z0-9_]+', identity)):
            raise StageBlocked('live_pending_graph_differs_from_rehearsal')
        observed.append(identity)
    if len(observed) != len(set(observed)) or set(observed) != set(reviewed):
        raise StageBlocked('live_pending_graph_differs_from_rehearsal')
    return observed


def verify_current_main(expected_sha, *, run=subprocess.run):
    if not _allowed_sha(expected_sha):
        raise StageBlocked('exact_source_sha_required')
    current = run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True, check=False)
    remote = run(['git', 'fetch', '--no-tags', 'origin', 'refs/heads/main:refs/remotes/origin/main'],
                 cwd=ROOT, capture_output=True, text=True, check=False)
    accepted = run(['git', 'rev-parse', 'refs/remotes/origin/main'], cwd=ROOT,
                   capture_output=True, text=True, check=False)
    if (current.returncode or remote.returncode or accepted.returncode
            or current.stdout.strip() != expected_sha or accepted.stdout.strip() != expected_sha):
        raise StageBlocked('protected_main_moved_or_unverified')


def execute_stage(expected_sha, receipt, *, get_dev_settings=None):
    """Transactional migration under the existing PostgreSQL advisory lock."""
    from rehearse_dev_heritage_migrations import (MIGRATIONS, SEED_TABLES, verify_manifest,
        table_facts, row_digest, seed_row_multiset, data_fingerprint)
    from run_dev_inquiry_migration import (load_dev_settings, validate_database_url,
                                            DEV_HOST, Blocked as DevConfigBlocked)
    verify_manifest()  # Exact 21 pinned file digests before Azure appsettings reads.
    receipt_contract(receipt, expected_sha)
    verify_current_main(expected_sha)
    load_settings = get_dev_settings or load_dev_settings
    try:
        url, secret, db_name, blacklist = load_settings()
        if blacklist or validate_database_url(url) != db_name:
            raise StageBlocked('dev_database_or_optional_graph_invalid')
        identity = hashlib.sha256((DEV_HOST+'/'+db_name).encode()).hexdigest()
        if receipt.get('source_database_identity_sha256') != identity:
            raise StageBlocked('restore_and_live_dev_database_identity_differs')
    except DevConfigBlocked:
        raise StageBlocked('dev_database_configuration_denied') from None
    ca = Path('/etc/ssl/certs/ca-certificates.crt')
    if not ca.is_file():
        raise StageBlocked('trusted_database_ca_unavailable')
    query = {'sslmode': 'verify-full', 'sslrootcert': str(ca), 'connect_timeout': 12}
    tls_url = urlsplit(url)._replace(query=urlencode(query)).geturl()
    os.environ.update(DATABASE_URL=tls_url, DJANGO_SECRET_KEY=secret,
                      DJANGO_SETTINGS_MODULE='crown_api.settings', CROWN_ENV='dev',
                      DJANGO_ENV='development', ENVIRONMENT='dev', DEBUG='false',
                      DJANGO_DEBUG='false', CROWN_SIMPLEJWT_BLACKLIST_ENABLED='false',
                      CROWN_DEMO_MODE='false', BUILD_SHA=expected_sha)
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        for value in (url, tls_url, secret):
            print('::add-mask::' + value.replace('%', '%25'), file=sys.__stdout__, flush=True)
    sys.path.insert(0, str(ROOT / 'backend'))
    import django
    django.setup()
    from django.apps import apps
    from django.db import connection, transaction
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.recorder import MigrationRecorder
    from core.management.commands.migrate_with_lock import Command
    if (connection.vendor != 'postgresql' or connection.settings_dict.get('HOST') != DEV_HOST
            or connection.settings_dict.get('NAME') != db_name or apps.is_installed('rest_framework_simplejwt.token_blacklist')):
        raise StageBlocked('live_dev_database_identity_denied')
    connection.settings_dict['OPTIONS'] = query
    connection.close()
    try:
        with Command()._migration_lock(timeout_seconds=300, allow_non_postgresql=False):
            with connection.cursor() as cursor:
                cursor.execute('SELECT current_database(),current_schema(),pg_is_in_recovery(),current_setting(\'server_version_num\')::integer')
                db, schema, recovery, version = cursor.fetchone()
                if (db, schema, recovery) != (db_name, 'public', False) or type(version) is not int or version // 10000 != 15:
                    raise StageBlocked('live_dev_database_identity_denied')
                cursor.execute('SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()')
                if cursor.fetchone() != (True,):
                    raise StageBlocked('live_database_tls_unverified')
                cursor.execute("SET lock_timeout = '15s'")
                cursor.execute("SET statement_timeout = '300s'")
                cursor.execute("SELECT has_schema_privilege(current_user,'public','CREATE')")
                if cursor.fetchone() != (True,):
                    raise StageBlocked('live_dev_ddl_authority_missing')
                cursor.execute("SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
                               "WHERE n.nspname='public' AND c.relkind IN ('r','p','S','v','m') "
                               "AND NOT pg_has_role(current_user,c.relowner,'USAGE')")
                unowned = cursor.fetchone()
                if not unowned or unowned[0] != 0:
                    raise StageBlocked('live_dev_ddl_table_ownership_unverified')
            executor = MigrationExecutor(connection)
            executor.loader.check_consistent_history(connection)
            if executor.loader.detect_conflicts():
                raise StageBlocked('migration_graph_conflict')
            targets = executor.loader.graph.leaf_nodes()
            plan = executor.migration_plan(targets)
            names = plan_contract(plan, MIGRATIONS)
            history = set(MigrationRecorder(connection).applied_migrations())
            columns = table_facts(connection)
            before = {table: row_digest(connection, table, names)
                      for table, names in columns.items()}
            seed_before = {table: seed_row_multiset(connection, table, columns[table])
                           for table in SEED_TABLES if table in columns}
            # Match the exact data baseline rehearsed on the disposable copy,
            # not merely its database name, migration graph or receipt shape.
            live_baseline_contract(receipt, data_fingerprint(columns, before),
                                   len(history), len(columns))
            verify_current_main(expected_sha)  # race protection immediately before schema mutation
            with transaction.atomic(using=connection.alias):
                executor.migrate(targets)
                after_history = set(MigrationRecorder(connection).applied_migrations())
                if after_history != history | {tuple(x.split('.', 1)) for x in names}:
                    raise StageBlocked('schema_migration_history_changed')
                if MigrationExecutor(connection).migration_plan(targets):
                    raise StageBlocked('schema_pending_after_migration')
                # Check original values before committing any live DDL. The
                # reviewed permission/feature seeds may add rows but may not
                # mutate or remove any existing entries.
                for table, names_for_table in columns.items():
                    after = row_digest(connection, table, names_for_table)
                    if table == 'django_migrations':
                        if after[0] != before[table][0] + EXPECTED_COUNT:
                            raise StageBlocked('migration_record_preservation_failed')
                    elif table in SEED_TABLES:
                        if seed_before[table] - seed_row_multiset(connection, table, names_for_table):
                            raise StageBlocked('existing_seed_data_changed')
                    elif after != before[table]:
                        raise StageBlocked('existing_dev_data_changed')
                # All DDL, migration-history writes and validation share PG15 transaction.
            return dict(result='PASS', source_sha=expected_sha,
                        applied_migrations_count=len(names), remaining_pending=0,
                        target_app=DEV_APP,
                        database_identity_sha256=identity,
                        original_values_preserved=True,
                        transaction_atomic=True,
                        new_resources_created=False, release_certified=False)
    finally:
        connection.close()
        for key in ('DATABASE_URL', 'DJANGO_SECRET_KEY'):
            os.environ.pop(key, None)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--confirmation', default='')
    parser.add_argument('--synthetic-dev-confirmed', default='false')
    parser.add_argument('--backup-recovery-verified', default='false')
    parser.add_argument('--maintenance-window-confirmed', default='false')
    parser.add_argument('--rehearsal-run-id', default='')
    parser.add_argument('--rehearsal-artifact-id', required=True)
    parser.add_argument('--evidence-path', default='')
    args = parser.parse_args(argv)
    status = dict(result='BLOCKED', source_sha=args.expected_sha if _allowed_sha(args.expected_sha) else None,
                  target_app=DEV_APP, release_certified=False, live_dev_schema_write_performed=False)
    try:
        authority(args.expected_sha, args.confirmation, args.synthetic_dev_confirmed,
                  args.backup_recovery_verified, args.maintenance_window_confirmed,
                  args.rehearsal_run_id, os.environ)
        receipt = authenticated_rehearsal_receipt(
            args.rehearsal_run_id, args.rehearsal_artifact_id, args.expected_sha, os.environ,
        )
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            outcome = execute_stage(args.expected_sha, receipt)
        status.update(outcome, live_dev_schema_write_performed=True)
    except Exception as exc:
        status['reason'] = str(exc) if isinstance(exc, StageBlocked) else 'dev_schema_stage_execution_blocked'
    finally:
        for key in ('DATABASE_URL','DJANGO_SECRET_KEY'):
            os.environ.pop(key, None)
    if args.evidence_path:
        path = Path(args.evidence_path)
        if (not path.is_absolute() or path.name != 'reviewed-dev-schema-stage.json'
                or not os.environ.get('RUNNER_TEMP')
                or path.parent != Path(os.environ['RUNNER_TEMP']).resolve()):
            raise StageBlocked('evidence_path_must_be_runner_temp')
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(status, handle, sort_keys=True)
            handle.write('\n')
    print(json.dumps(status, sort_keys=True))
    return 0 if status['result']=='PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
