"""Read-only schema boundary for the separately authorized legacy refresh DEV migration.

This module never opens a connection or performs writes. Token digests and rows
are neither read nor returned. Running the ordinary DEV deploy does not opt in.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REVIEWED = ("crown_api", "0014_legacy_refresh_consumption")
MIGRATION_SHA256 = "73ded6932f7aa1e6e54d8922aecdb4ca62d41ecde2aff4f6a15ca988d03b1f71"
TABLE = "crown_api_legacyrefreshconsumption"
CROWN_USER_TABLE = "crown_api_crownuser"
COLUMNS = {"id", "token_digest", "consumed_at", "expires_at", "user_id"}


class LegacyBoundaryError(RuntimeError):
    """Fixed, non-sensitive reason codes for controlled migration evidence."""


def verify_source(root: Path) -> None:
    path = root / "backend" / REVIEWED[0] / "migrations" / (REVIEWED[1] + ".py")
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != MIGRATION_SHA256:
        raise LegacyBoundaryError("reviewed_legacy_migration_digest_mismatch")


def validate_plan(plan):
    """Only an empty plan or the single forward reviewed migration is allowed."""
    identities = [(node.app_label, node.name) for node, backwards in plan if not backwards]
    if any(backwards for _, backwards in plan) or identities not in ([], [REVIEWED]):
        raise LegacyBoundaryError("unreviewed_legacy_pending_migrations")
    return identities


def preflight(connection, loader) -> None:
    """Reject untracked/partial history before any schema-changing command."""
    if REVIEWED not in loader.disk_migrations:
        raise LegacyBoundaryError("reviewed_legacy_migration_missing")
    recorded = REVIEWED in loader.applied_migrations
    exists = TABLE in connection.introspection.table_names()
    if exists and not recorded:
        raise LegacyBoundaryError("untracked_legacy_refresh_table")
    if recorded and not exists:
        raise LegacyBoundaryError("recorded_legacy_refresh_table_missing")
    if recorded:
        verify_applied_schema(connection)


def verify_applied_schema(connection) -> None:
    """Inspect only Django migration metadata and the required table constraints."""
    from django.db.migrations.recorder import MigrationRecorder

    if REVIEWED not in MigrationRecorder(connection).applied_migrations():
        raise LegacyBoundaryError("legacy_refresh_migration_not_applied")
    if TABLE not in connection.introspection.table_names():
        raise LegacyBoundaryError("legacy_refresh_table_missing")
    with connection.cursor() as cursor:
        columns = {col.name for col in connection.introspection.get_table_description(cursor, TABLE)}
        if not COLUMNS.issubset(columns):
            raise LegacyBoundaryError("legacy_refresh_columns_missing")
        constraints = connection.introspection.get_constraints(cursor, TABLE)
    if not any(c.get("unique") and c.get("columns") == ["token_digest"] for c in constraints.values()):
        raise LegacyBoundaryError("legacy_refresh_digest_unique_missing")
    if not any(c.get("foreign_key") == (CROWN_USER_TABLE, "id") and c.get("columns") == ["user_id"]
               for c in constraints.values()):
        raise LegacyBoundaryError("legacy_refresh_user_foreign_key_missing")
    if not any(c.get("index") and c.get("columns") == ["expires_at"] for c in constraints.values()):
        raise LegacyBoundaryError("legacy_refresh_expiry_index_missing")
