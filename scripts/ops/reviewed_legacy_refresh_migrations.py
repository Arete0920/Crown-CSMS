"""Read-only schema boundary for the separately authorized legacy refresh DEV migration.

This module never opens a connection or performs writes. Token digests and rows
are neither read nor returned. Running the ordinary DEV deploy does not opt in.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

REVIEWED = ("crown_api", "0014_legacy_refresh_consumption")
MIGRATION_SHA256 = "73ded6932f7aa1e6e54d8922aecdb4ca62d41ecde2aff4f6a15ca988d03b1f71"
INQUIRY = ("crm_marketing", "0002_inquiry_capture")
INQUIRY_SHA256 = "b4224adf8e10c05e836a164200ff6c0552067491006c8dc2fc3a3095cc7743eb"
TABLE = "crown_api_legacyrefreshconsumption"
CROWN_USER_TABLE = "crown_api_crownuser"
COLUMNS = {"id", "token_digest", "consumed_at", "expires_at", "user_id"}


class LegacyBoundaryError(RuntimeError):
    """Fixed, non-sensitive reason codes for controlled migration evidence."""


def verify_source(root: Path) -> None:
    for identity, digest, label in (
        (REVIEWED, MIGRATION_SHA256, "legacy"),
        (INQUIRY, INQUIRY_SHA256, "inquiry"),
    ):
        path = root / "backend" / identity[0] / "migrations" / (identity[1] + ".py")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise LegacyBoundaryError(f"reviewed_{label}_migration_digest_mismatch")


def validate_plan(plan):
    """Allow the legacy migration, optionally after the exact reviewed inquiry."""
    identities = [(node.app_label, node.name) for node, backwards in plan if not backwards]
    if any(backwards for _, backwards in plan) or identities not in (
        [], [REVIEWED], [INQUIRY, REVIEWED],
    ):
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
