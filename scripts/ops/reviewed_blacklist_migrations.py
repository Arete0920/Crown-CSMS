"""Exact-version and schema guards for the SimpleJWT 5.5.1 DEV rollout.

No credentials, token contents, row values, or personal records are inspected.
This module does not initiate a connection or execute a migration by itself.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


VENDOR_DISTRIBUTION = "djangorestframework-simplejwt"
REVIEWED_VERSION = "5.5.1"
APP_CONFIG = "rest_framework_simplejwt.token_blacklist"
APP_LABEL = "token_blacklist"
OUTSTANDING_TABLE = "token_blacklist_outstandingtoken"
BLACKLISTED_TABLE = "token_blacklist_blacklistedtoken"

# Verified against the upstream SimpleJWT v5.5.1 release. There is no 0009.
MIGRATION_NAMES = (
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


class BlacklistBoundaryError(RuntimeError):
    """Fixed non-sensitive error code suitable for controlled CI evidence."""


def validate_source_state(*, runtime_version, disk_names, applied_names, table_names):
    """Require the reviewed vendor graph and a contiguous recorded history."""
    if runtime_version != REVIEWED_VERSION:
        raise BlacklistBoundaryError("unreviewed_simplejwt_runtime_version")
    expected = set(MIGRATION_NAMES)
    if set(disk_names) != expected:
        raise BlacklistBoundaryError("unreviewed_simplejwt_migration_graph")
    applied = set(applied_names)
    if applied != set(MIGRATION_NAMES[:len(applied)]):
        raise BlacklistBoundaryError("noncanonical_blacklist_migration_history")

    existing = {OUTSTANDING_TABLE, BLACKLISTED_TABLE}.intersection(table_names)
    if applied and existing != {OUTSTANDING_TABLE, BLACKLISTED_TABLE}:
        raise BlacklistBoundaryError("blacklist_history_schema_mismatch")
    if not applied and existing:
        raise BlacklistBoundaryError("untracked_blacklist_tables")
    return True


def is_reviewed_plan(plan, *, allow_blacklist=False):
    """Only permit the exact vendor forward suffix (if explicitly enabled)."""
    if not allow_blacklist:
        return not any(node.app_label == APP_LABEL for node, _ in plan)
    listed = tuple((node.app_label, node.name) for node, backwards in plan
                   if node.app_label == APP_LABEL and not backwards)
    expected = tuple((APP_LABEL, name) for name in MIGRATION_NAMES)
    return listed == () or any(listed == expected[index:]
                               for index in range(len(expected)))


def preflight(connection, loader, *, installed):
    """Read-only graph, recorder, and schema checks under the existing lock."""
    if not installed:
        return False
    try:
        installed_version = version(VENDOR_DISTRIBUTION)
    except PackageNotFoundError as exc:
        raise BlacklistBoundaryError("simplejwt_distribution_unavailable") from exc
    disk = {name for app, name in loader.disk_migrations if app == APP_LABEL}
    applied = {name for app, name in loader.applied_migrations if app == APP_LABEL}
    validate_source_state(
        runtime_version=installed_version,
        disk_names=disk,
        applied_names=applied,
        table_names=set(connection.introspection.table_names()),
    )
    return True


def verify_applied_schema(connection):
    """Verify the vendor migration chain, required columns, and unique keys."""
    from django.db.migrations.recorder import MigrationRecorder

    applied = {
        name for app, name in MigrationRecorder(connection).applied_migrations()
        if app == APP_LABEL
    }
    if applied != set(MIGRATION_NAMES):
        raise BlacklistBoundaryError("blacklist_migrations_not_complete")

    tables = set(connection.introspection.table_names())
    if {OUTSTANDING_TABLE, BLACKLISTED_TABLE} - tables:
        raise BlacklistBoundaryError("blacklist_tables_missing")

    requirements = (
        (OUTSTANDING_TABLE, {"id", "user_id", "jti", "token", "created_at", "expires_at"}, "jti"),
        (BLACKLISTED_TABLE, {"id", "token_id", "blacklisted_at"}, "token_id"),
    )
    with connection.cursor() as cursor:
        for table, required_columns, unique_column in requirements:
            actual_columns = {
                col.name
                for col in connection.introspection.get_table_description(cursor, table)
            }
            if not required_columns.issubset(actual_columns):
                raise BlacklistBoundaryError("blacklist_columns_missing")
            constraints = connection.introspection.get_constraints(cursor, table)
            unique_found = any(
                item.get("unique") and item.get("columns") == [unique_column]
                for item in constraints.values()
            )
            if not unique_found:
                raise BlacklistBoundaryError("blacklist_unique_constraint_missing")
