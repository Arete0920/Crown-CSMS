"""Apply the reviewed inquiry migration on the existing DEV database only.

Called by deploy-dev after accepted-source verification and existing DEV login.
No provider messages, resource creation, configuration writes or startup flags.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit


ROOT = Path(__file__).resolve().parents[2]
DEV_APP = "crown-api-dev"
DEV_HOST = "crown-pg-dev.postgres.database.azure.com"
REVIEWED = ("crm_marketing", "0002_inquiry_capture")
MIGRATION_SHA256 = "b4224adf8e10c05e836a164200ff6c0552067491006c8dc2fc3a3095cc7743eb"


class Blocked(RuntimeError):
    """Only fixed, non-sensitive reason codes may reach the evidence output."""


class UnreviewedPlan(Blocked):
    def __init__(self, plan):
        super().__init__("unreviewed_pending_migrations")

        def identifier(value):
            return value if isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_]{1,128}", value) else "[invalid]"

        self.evidence = {
            "pending_migrations": [
                {"app": identifier(item.app_label), "migration": identifier(item.name),
                 "direction": "backward" if backwards else "forward"}
                for item, backwards in plan[:20]
            ],
            "pending_migrations_count": len(plan),
            "pending_migrations_truncated": len(plan) > 20,
        }


def read_azure(*arguments):
    result = subprocess.run(
        ["az", *arguments, "--only-show-errors", "--output", "json"],
        capture_output=True, text=True, timeout=90, check=False,
    )
    if result.returncode:
        raise Blocked("azure_read_unavailable")
    return json.loads(result.stdout)


def validate_source(expected_sha, *, root=ROOT, run=subprocess.run, reviewed_legacy=False):
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        raise Blocked("full_source_sha_required")
    head = run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    ancestry = run(["git", "merge-base", "--is-ancestor", expected_sha, "origin/main"],
                   cwd=root, capture_output=True, text=True, check=False)
    if head.returncode or head.stdout.strip() != expected_sha or ancestry.returncode:
        raise Blocked("source_not_accepted_main_commit")
    migration = root / "backend" / REVIEWED[0] / "migrations" / (REVIEWED[1] + ".py")
    if not migration.is_file() or hashlib.sha256(migration.read_bytes()).hexdigest() != MIGRATION_SHA256:
        raise Blocked("reviewed_migration_digest_mismatch")
    if reviewed_legacy:
        from reviewed_legacy_refresh_migrations import (
            LegacyBoundaryError, verify_source as verify_legacy_source,
        )
        try:
            verify_legacy_source(root)
        except LegacyBoundaryError as exc:
            raise Blocked(str(exc)) from exc


def resolve_value(raw, *, read=read_azure):
    if not isinstance(raw, str) or not raw or any(char in raw for char in "\r\n"):
        raise Blocked("dev_configuration_unavailable")
    if not raw.startswith("@Microsoft.KeyVault("):
        return raw
    if not raw.endswith(")"):
        raise Blocked("unsupported_key_vault_reference")
    fields = {}
    for part in raw[20:-1].split(";"):
        if "=" not in part:
            raise Blocked("unsupported_key_vault_reference")
        key, value = (item.strip() for item in part.split("=", 1))
        if key in fields:
            raise Blocked("unsupported_key_vault_reference")
        fields[key] = value
    if fields.get("SecretUri"):
        uri = urlsplit(fields["SecretUri"])
        if (uri.scheme != "https" or not re.fullmatch(r"[A-Za-z0-9-]+\.vault\.azure\.net", uri.hostname or "")
                or uri.username or uri.password or uri.port not in (None, 443) or uri.query or uri.fragment
                or not re.fullmatch(r"/secrets/[A-Za-z0-9-]+(?:/[A-Za-z0-9-]+)?", uri.path)):
            raise Blocked("unsupported_key_vault_reference")
        result = read("keyvault", "secret", "show", "--id", fields["SecretUri"])
    else:
        if not all(re.fullmatch(r"[A-Za-z0-9-]+", fields.get(key, "")) for key in ("VaultName", "SecretName")):
            raise Blocked("unsupported_key_vault_reference")
        result = read("keyvault", "secret", "show", "--vault-name", fields["VaultName"], "--name", fields["SecretName"])
    value = result.get("value") if isinstance(result, dict) else None
    if not isinstance(value, str) or not value or any(char in value for char in "\r\n"):
        raise Blocked("dev_configuration_unavailable")
    return value


def validate_database_url(database_url):
    target = urlsplit(database_url)
    name = unquote(target.path.removeprefix("/"))
    query = parse_qsl(target.query, keep_blank_values=True, strict_parsing=True)
    if (target.scheme not in {"postgres", "postgresql"} or target.hostname != DEV_HOST
            or target.port not in (None, 5432) or not target.username or not target.password
            or target.fragment or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_$.-]{0,62}", name)
            or name.lower() in {"postgres", "template0", "template1", "azure_maintenance"}
            or len(query) > 1 or any(key != "sslmode" or value not in {"require", "verify-ca", "verify-full"} for key, value in query)):
        raise Blocked("database_target_not_verified_dev")
    return name


def load_dev_settings(*, read=read_azure, legacy_stage=False):
    target = ["--resource-group", "crown-rg", "--name", DEV_APP]
    app = read("webapp", "show", *target, "--query", "{name:name,defaultHostName:defaultHostName}")
    if not isinstance(app, dict) or app.get("name") != DEV_APP or app.get("defaultHostName") != DEV_APP + ".azurewebsites.net":
        raise Blocked("dev_app_identity_not_verified")
    rows = read("webapp", "config", "appsettings", "list", *target)
    if not isinstance(rows, list) or any(not isinstance(row, dict) or not isinstance(row.get("name"), str) for row in rows):
        raise Blocked("dev_configuration_unavailable")
    if len({row["name"] for row in rows}) != len(rows):
        raise Blocked("duplicate_configuration_names")
    values = {row["name"]: row.get("value") for row in rows}
    if values.get("CROWN_ENV") != "dev" or values.get("ENVIRONMENT") != "dev" or values.get("DJANGO_ENV") != "development":
        raise Blocked("dev_environment_markers_not_verified")
    database_url = resolve_value(values.get("DATABASE_URL"), read=read)
    database_name = validate_database_url(database_url)
    secret = resolve_value(values.get("DJANGO_SECRET_KEY") or values.get("SECRET_KEY"), read=read)
    # Preserve the actual hosted activation state. Ordinary deployments must
    # validate an already enabled target rather than silently disabling the
    # blacklist app in the isolated migration preflight process.
    raw_blacklist = values.get("CROWN_SIMPLEJWT_BLACKLIST_ENABLED", "false")
    if not isinstance(raw_blacklist, str):
        raise Blocked("invalid_dev_blacklist_setting")
    flag = raw_blacklist.strip().lower()
    if flag not in {"", "0", "false", "no", "off", "1", "true", "yes", "on"}:
        raise Blocked("invalid_dev_blacklist_setting")
    hosted_blacklist_enabled = flag in {"1", "true", "yes", "on"}
    if legacy_stage:
        # Fail closed if one-use runtime traffic is already using this schema.
        raw_legacy = values.get("CROWN_LEGACY_REFRESH_ONE_USE_ENABLED", "false")
        if (not isinstance(raw_legacy, str) or
                raw_legacy.strip().lower() not in {"", "0", "false", "no", "off"}):
            raise Blocked("legacy_refresh_must_be_disabled_for_schema_stage")
    return database_url, secret, database_name, hosted_blacklist_enabled


def validate_plan(plan):
    identities = [(item.app_label, item.name) for item, backwards in plan if not backwards]
    if any(backwards for _, backwards in plan) or identities not in ([], [REVIEWED]):
        raise UnreviewedPlan(plan)
    return identities


def validate_blacklist_plan(plan):
    # The explicit DEV schema stage accepts *only* a contiguous upstream
    # SimpleJWT 5.5.1 migration suffix; no unrelated or backwards migrations.
    from reviewed_blacklist_migrations import is_reviewed_plan

    if not is_reviewed_plan(plan, allow_blacklist=True):
        raise UnreviewedPlan(plan)
    return [(item.app_label, item.name) for item, _ in plan]


def validate_legacy_plan(plan):
    from reviewed_legacy_refresh_migrations import (
        LegacyBoundaryError, validate_plan as validate_legacy_boundary_plan,
    )
    try:
        return validate_legacy_boundary_plan(plan)
    except LegacyBoundaryError as exc:
        raise UnreviewedPlan(plan) from exc


def apply_reviewed_plan(*, acquire_lock, verify_identity, verify_ddl, read_plan,
                        invoke, check_only=False, plan_validator=validate_plan,
                        post_verify=None):
    # Hold the existing advisory lock across planning, its reentrant command,
    # and verification so another governed migration cannot race this allowlist.
    with acquire_lock():
        verify_identity()
        pending = plan_validator(read_plan())
        if check_only:
            # Read the verified migration plan; never invoke schema-changing commands.
            return [".".join(item) for item in pending]
        if pending:
            verify_ddl()
        invoke("migrate_with_lock", lock_timeout_seconds=300, check=not bool(pending))
        invoke("migrate", check=True, interactive=False)
        if read_plan():
            raise Blocked("pending_migrations_after_verification")
        if post_verify is not None:
            post_verify()
    return [".".join(item) for item in pending]


def migrate_on_dev(database_url, secret, database_name, source_sha, *,
                   check_only=False, apply_blacklist=False, hosted_blacklist_enabled=False,
                   legacy_stage=False):
    if (check_only and apply_blacklist) or (apply_blacklist and legacy_stage):
        raise Blocked("conflicting_dev_migration_modes")
    if not isinstance(hosted_blacklist_enabled, bool):
        raise Blocked("invalid_dev_blacklist_setting")
    if validate_database_url(database_url) != database_name:
        raise Blocked("effective_database_target_mismatch")
    ca_bundle = Path("/etc/ssl/certs/ca-certificates.crt")
    if not ca_bundle.is_file():
        raise Blocked("trusted_database_ca_unavailable")
    options = {"sslmode": "verify-full", "sslrootcert": str(ca_bundle), "connect_timeout": 15}
    # Enforce verified TLS before Django loads any application ready() hooks.
    runner_url = urlsplit(database_url)._replace(query=urlencode(options)).geturl()
    # Credentials live only in this process; never write them to artifacts or
    # GITHUB_ENV, and never inherit production credential fallbacks.
    os.environ.update(DATABASE_URL=runner_url, DJANGO_SECRET_KEY=secret,
                      DJANGO_SETTINGS_MODULE="crown_api.settings", CROWN_ENV="dev",
                      DJANGO_ENV="development", ENVIRONMENT="dev", DJANGO_DEBUG="false",
                      DEBUG="false", BUILD_SHA=source_sha,
                      CROWN_SIMPLEJWT_BLACKLIST_ENABLED=(
                          "true" if (apply_blacklist or (check_only and not legacy_stage)
                                     or hosted_blacklist_enabled) else "false"
                      ))
    if legacy_stage:
        # Never activate one-use behavior when its schema is being examined/staged.
        os.environ["CROWN_LEGACY_REFRESH_ONE_USE_ENABLED"] = "false"
    sys.path.insert(0, str(ROOT / "backend"))
    import django
    django.setup()
    from django.db import connection
    from django.core.management import call_command
    from django.db.migrations.executor import MigrationExecutor
    from core.management.commands.migrate_with_lock import Command
    from django.apps import apps
    from reviewed_blacklist_migrations import (
        preflight as validate_blacklist_preflight,
        verify_applied_schema,
        BlacklistBoundaryError,
    )
    from reviewed_legacy_refresh_migrations import (
        LegacyBoundaryError,
        preflight as validate_legacy_preflight,
        verify_applied_schema as verify_legacy_applied_schema,
    )

    config = connection.settings_dict
    if (connection.vendor != "postgresql" or config.get("HOST") != DEV_HOST
            or config.get("NAME") != database_name or str(config.get("PORT") or "5432") != "5432"):
        raise Blocked("effective_database_target_mismatch")
    config["OPTIONS"] = options
    connection.close()

    def verify_identity():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_schema(), pg_is_in_recovery()")
            if cursor.fetchone() != (database_name, "public", False):
                raise Blocked("connected_database_identity_mismatch")
            cursor.execute("SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()")
            if cursor.fetchone() != (True,):
                raise Blocked("database_tls_not_verified")
            cursor.execute("SET lock_timeout = '15s'")
            cursor.execute("SET statement_timeout = '300s'")

    def verify_ddl():
        with connection.cursor() as cursor:
            if legacy_stage:
                cursor.execute(
                    "SELECT has_schema_privilege(current_user, 'public', 'CREATE'), "
                    "has_table_privilege(current_user, "
                    "'public.crown_api_crownuser', 'REFERENCES')"
                )
                if cursor.fetchone() != (True, True):
                    raise Blocked("legacy_refresh_database_ddl_authority_unavailable")
                return
            if apply_blacklist:
                cursor.execute(
                    "SELECT has_schema_privilege(current_user, 'public', 'CREATE'), "
                    "has_table_privilege(current_user, "
                    "'public.core_useraccount', 'REFERENCES')"
                )
                if cursor.fetchone() != (True, True):
                    raise Blocked("blacklist_database_ddl_authority_unavailable")
                return
            cursor.execute("SELECT has_schema_privilege(current_user, 'public', 'CREATE'), "
                           "pg_has_role(current_user, relowner, 'USAGE') FROM pg_class "
                           "WHERE oid = to_regclass('public.crm_marketing_marketinglead')")
            if cursor.fetchone() != (True, True):
                raise Blocked("existing_database_ddl_authority_unavailable")

    def read_plan():
        executor = MigrationExecutor(connection)
        executor.loader.check_consistent_history(connection)
        try:
            validate_blacklist_preflight(
                connection,
                executor.loader,
                installed=apps.is_installed('rest_framework_simplejwt.token_blacklist'),
            )
        except BlacklistBoundaryError as exc:
            raise Blocked(str(exc)) from exc
        if legacy_stage:
            try:
                validate_legacy_preflight(connection, executor.loader)
            except LegacyBoundaryError as exc:
                raise Blocked(str(exc)) from exc
        if executor.loader.detect_conflicts():
            raise Blocked("migration_graph_conflict")
        return executor.migration_plan(executor.loader.graph.leaf_nodes())

    try:
        return apply_reviewed_plan(
            acquire_lock=lambda: Command()._migration_lock(timeout_seconds=300, allow_non_postgresql=False),
            verify_identity=verify_identity, verify_ddl=verify_ddl, read_plan=read_plan,
            invoke=call_command, check_only=check_only,
            plan_validator=(validate_blacklist_plan if apply_blacklist else
                            validate_legacy_plan if legacy_stage else validate_plan),
            post_verify=((lambda: verify_applied_schema(connection)) if apply_blacklist else
                         (lambda: verify_legacy_applied_schema(connection)) if
                         legacy_stage and not check_only else None),
        )
    finally:
        connection.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--check-only", action="store_true",
                        help="Read-only DEV migration preflight; never apply migrations")
    parser.add_argument("--apply-reviewed-blacklist", action="store_true",
                        help="Explicit guarded DEV-only SimpleJWT schema stage")
    parser.add_argument("--confirm-dev-blacklist", default="",
                        help="Must equal migrate-dev-blacklist for explicit DEV schema stage")
    parser.add_argument("--inspect-reviewed-legacy-refresh", action="store_true",
                        help="DEV legacy schema plan inspection only; never mutate")
    parser.add_argument("--apply-reviewed-legacy-refresh", action="store_true",
                        help="Explicit guarded DEV-only legacy refresh schema stage")
    parser.add_argument("--confirm-dev-legacy-refresh", default="",
                        help="Must equal migrate-dev-legacy-refresh to apply schema")
    args = parser.parse_args(argv)
    stage = "source"
    try:
        legacy_stage = args.inspect_reviewed_legacy_refresh or args.apply_reviewed_legacy_refresh
        if ((args.check_only and (args.apply_reviewed_blacklist or legacy_stage))
                or (args.apply_reviewed_blacklist and legacy_stage)
                or (args.inspect_reviewed_legacy_refresh and args.apply_reviewed_legacy_refresh)):
            raise Blocked("conflicting_dev_migration_modes")
        if args.apply_reviewed_blacklist != (args.confirm_dev_blacklist == "migrate-dev-blacklist"):
            raise Blocked("explicit_dev_blacklist_authority_required")
        if args.confirm_dev_blacklist and not args.apply_reviewed_blacklist:
            raise Blocked("explicit_dev_blacklist_authority_required")
        if (args.apply_reviewed_legacy_refresh !=
                (args.confirm_dev_legacy_refresh == "migrate-dev-legacy-refresh")):
            raise Blocked("explicit_dev_legacy_authority_required")
        if args.confirm_dev_legacy_refresh and not args.apply_reviewed_legacy_refresh:
            raise Blocked("explicit_dev_legacy_authority_required")
        if legacy_stage:
            validate_source(args.expected_sha, reviewed_legacy=True)
        else:
            validate_source(args.expected_sha)
        stage = "dev_configuration"
        if legacy_stage:
            database_url, secret, database_name, hosted_blacklist_enabled = load_dev_settings(legacy_stage=True)
        else:
            database_url, secret, database_name, hosted_blacklist_enabled = load_dev_settings()
        # GitHub masking commands are consumed by the runner, not evidence files.
        # GitHub Actions consumes add-mask workflow commands. Printing them in a
        # local operator terminal would disclose the raw DB URL and Django key.
        if os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true":
            for value in (database_url, secret):
                print("::add-mask::" + value.replace("%", "%25"), flush=True)
        stage = "database_plan_and_migration"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            if args.inspect_reviewed_legacy_refresh:
                applied = migrate_on_dev(database_url, secret, database_name,
                                         args.expected_sha, check_only=True, legacy_stage=True,
                                         hosted_blacklist_enabled=hosted_blacklist_enabled)
            elif args.check_only:
                applied = migrate_on_dev(database_url, secret, database_name,
                                         args.expected_sha, check_only=True)
            elif args.apply_reviewed_blacklist:
                applied = migrate_on_dev(database_url, secret, database_name,
                                         args.expected_sha, apply_blacklist=True)
            elif args.apply_reviewed_legacy_refresh:
                applied = migrate_on_dev(database_url, secret, database_name,
                                         args.expected_sha, legacy_stage=True,
                                         hosted_blacklist_enabled=hosted_blacklist_enabled)
            else:
                applied = migrate_on_dev(database_url, secret, database_name, args.expected_sha,
                                         hosted_blacklist_enabled=hosted_blacklist_enabled)
        result = {"status": "PASS", "source_sha": args.expected_sha, "target_app": DEV_APP,
                  "mode": ("read_only" if args.check_only else
                           "reviewed_dev_legacy_inspect" if args.inspect_reviewed_legacy_refresh else
                           "reviewed_dev_legacy_apply" if args.apply_reviewed_legacy_refresh else
                           "reviewed_dev_blacklist" if args.apply_reviewed_blacklist else "migrate"),
                  "database_identity_verified": True,
                  "database_identity_sha256": hashlib.sha256((DEV_HOST + "/" + database_name).encode()).hexdigest()}
        if args.check_only or args.inspect_reviewed_legacy_refresh:
            result.update(reviewed_pending_migrations=applied, remaining_pending=len(applied))
        else:
            result.update(applied_migrations=applied, remaining_pending=0)
    except (Exception, SystemExit) as exc:
        result = {"status": "BLOCKED",
                  "mode": ("read_only" if args.check_only else
                           "reviewed_dev_legacy_inspect" if args.inspect_reviewed_legacy_refresh else
                           "reviewed_dev_legacy_apply" if args.apply_reviewed_legacy_refresh else
                           "reviewed_dev_blacklist" if args.apply_reviewed_blacklist else "migrate"),
                  "stage": stage,
                  "source_sha": args.expected_sha if re.fullmatch(r"[0-9a-f]{40}", args.expected_sha) else None,
                  "target_app": DEV_APP,
                  "reason": str(exc) if isinstance(exc, Blocked) else "dependency_or_execution_failed"}
        if isinstance(exc, UnreviewedPlan):
            result.update(exc.evidence)
    finally:
        for name in ("DATABASE_URL", "DJANGO_SECRET_KEY"):
            os.environ.pop(name, None)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
