"""Strict DEV-only support schema stage, separate from the ordinary deploy gate.

Support 0002 and its backward-compatible database default (0003) must be
committed together so the previously deployed image never sees an intermediate
NOT NULL column without a server-side default. No production target is allowed.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

INQUIRY = ("crm_marketing", "0002_inquiry_capture")
LEGACY = ("crown_api", "0014_legacy_refresh_consumption")
SUPPORT_2 = ("support", "0002_ticket_attribution")
SUPPORT_3 = ("support", "0003_preserve_legacy_ticket_inserts")
TARGET = SUPPORT_3
PINNED_SUPPORT = (
    (SUPPORT_2, "9aae3963920e80e095c5a2f1d9d6c73dea5abcfc22010cebe628bce9ca2d579f"),
    (SUPPORT_3, "f088bc7ee588ea715efa734b3950b10e54e3bdf18df346adaa15505d55af5343"),
)
TICKET_TABLE = "support_supportticket"
EVENT_TABLE = "support_supportticketevent"


class SupportBoundaryError(RuntimeError):
    """Only fixed, non-sensitive migration-boundary reasons may be reported."""


def verify_source(root: Path) -> None:
    """Pin both migrations to reviewed bytes; never rewrite applied history."""
    for (app, name), expected_digest in PINNED_SUPPORT:
        file = root / "backend" / app / "migrations" / (name + ".py")
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected_digest:
            raise SupportBoundaryError("reviewed_support_migration_digest_mismatch")


def validate_plan(plan):
    """Allow only the observed, ordered exact migration set and its safe suffix.

    CRM/legacy are still owned by a separate explicit stage. Support 0002
    may execute only together with 0003 inside one PostgreSQL transaction.
    """
    identities = [(node.app_label, node.name) for node, backwards in plan if not backwards]
    if any(backwards for _, backwards in plan):
        raise SupportBoundaryError("unreviewed_dev_support_pending_migrations")
    prefixes = ((), (INQUIRY,), (LEGACY,), (INQUIRY, LEGACY))
    suffixes = ((), (SUPPORT_2, SUPPORT_3), (SUPPORT_3,))
    if not any(identities == list(prefix + suffix)
               for prefix in prefixes for suffix in suffixes):
        raise SupportBoundaryError("unreviewed_dev_support_pending_migrations")
    return identities


def validate_starting_schema(connection, loader):
    """Reject partially applied or unrecorded support schema before running."""
    recorded = loader.applied_migrations
    disk = loader.disk_migrations
    if SUPPORT_2 not in disk or SUPPORT_3 not in disk:
        raise SupportBoundaryError("reviewed_support_migrations_missing")
    if SUPPORT_3 in recorded and SUPPORT_2 not in recorded:
        raise SupportBoundaryError("support_history_out_of_order")
    tables = set(connection.introspection.table_names())
    if TICKET_TABLE not in tables:
        raise SupportBoundaryError("support_ticket_table_missing")
    exists = EVENT_TABLE in tables
    if exists != (SUPPORT_2 in recorded):
        raise SupportBoundaryError("support_event_history_mismatch")
    if SUPPORT_3 in recorded:
        verify_final_schema(connection)


def verify_ddl_authority(connection):
    """Require ownership of the existing ticket table and CREATE/FK authority."""
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT has_schema_privilege(current_user, 'public', 'CREATE'), "
            "pg_has_role(current_user, relowner, 'USAGE') "
            "FROM pg_class WHERE oid = to_regclass('public.support_supportticket')"
        )
        if cursor.fetchone() != (True, True):
            raise SupportBoundaryError("support_database_ddl_authority_unavailable")
        cursor.execute(
            "SELECT has_table_privilege(current_user, "
            "'public.core_useraccount', 'REFERENCES')"
        )
        if cursor.fetchone() != (True,):
            raise SupportBoundaryError("support_user_reference_authority_unavailable")


def verify_final_schema(connection):
    """Verify the server-side default needed by the still-running old image."""
    from django.db.migrations.recorder import MigrationRecorder

    recorded = MigrationRecorder(connection).applied_migrations()
    if SUPPORT_2 not in recorded or SUPPORT_3 not in recorded:
        raise SupportBoundaryError("support_migrations_not_applied")
    tables = set(connection.introspection.table_names())
    if not {TICKET_TABLE, EVENT_TABLE}.issubset(tables):
        raise SupportBoundaryError("support_tables_missing")
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT column_default, is_nullable FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='support_supportticket' "
            "AND column_name='resolution_summary'"
        )
        default_row = cursor.fetchone()
        cursor.execute(
            "SELECT is_nullable FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name='support_supportticket' "
            "AND column_name='requester_id'"
        )
        requester = cursor.fetchone()
    if (not default_row or default_row[1] != "NO"
            or not isinstance(default_row[0], str)
            or not default_row[0].startswith("''::")
            or default_row[0].split("::", 1)[1] not in ("text", "character varying")):
        raise SupportBoundaryError("support_legacy_insert_default_not_verified")
    if requester != ("YES",):
        raise SupportBoundaryError("support_requester_nullable_not_verified")
    with connection.cursor() as cursor:
        event_columns = {
            col.name for col in connection.introspection.get_table_description(cursor, EVENT_TABLE)
        }
    if not {"id", "ticket_id", "actor_id", "action", "created_at"}.issubset(event_columns):
        raise SupportBoundaryError("support_event_columns_missing")


def apply_support_stage(*, acquire_lock, verify_identity, read_plan,
                        migrate_support, verify_ddl, verify_after, atomic):
    """Apply only support 0002+0003 atomically; never apply CRM or JWT schema.

    Both Django migration records and PostgreSQL DDL are in one transaction.
    A migration or postcondition failure rolls everything back.
    """
    with acquire_lock():
        verify_identity()
        pending = validate_plan(read_plan())
        support_pending = [item for item in pending if item[0] == "support"]
        if not support_pending:
            verify_after()
            return []
        verify_ddl()
        with atomic():
            migrate_support()
            remaining = validate_plan(read_plan())
            if any(item[0] == "support" for item in remaining):
                raise SupportBoundaryError("support_migrations_remain_pending")
            verify_after()
        return [".".join(item) for item in support_pending]
