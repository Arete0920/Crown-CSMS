"""Real PostgreSQL proof of the bounded support stage; never a hosted DB drill."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
import uuid

import pytest
from django.core.management import call_command
from django.db import close_old_connections, connection, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder


@pytest.mark.django_db(transaction=True)
def test_support_stage_rolls_back_and_serializes_without_applying_other_migrations(
    monkeypatch,
):
    """Use actual DDL, records and locks; leave unrelated migration work pending."""
    if connection.vendor != "postgresql":
        pytest.skip("Support stage transaction proof requires real PostgreSQL")
    assert connection.settings_dict["HOST"] in {"localhost", "127.0.0.1"}
    assert str(connection.settings_dict["NAME"]).startswith("test_")

    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root / "scripts" / "ops"))
    import reviewed_dev_support_migrations as stage
    from core.management.commands.migrate_with_lock import Command
    from support.models import SupportTicket

    stage.verify_source(root)
    executor = MigrationExecutor(connection)
    final_targets = executor.loader.graph.leaf_nodes()
    previous_targets = [
        ("support", "0001_initial"),
        ("crm_marketing", "0001_initial"),
        ("crown_api", "0013_attendance_section"),
    ]
    commands = []

    def read_plan():
        current = MigrationExecutor(connection)
        current.loader.check_consistent_history(connection)
        stage.validate_starting_schema(connection, current.loader)
        return current.migration_plan(current.loader.graph.leaf_nodes())

    def verify_identity():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_schema()")
            assert cursor.fetchone() == (connection.settings_dict["NAME"], "public")

    def migrate_support():
        commands.append("support-only")
        call_command(
            "migrate", "support", stage.TARGET[1], interactive=False, verbosity=0,
        )

    def execute(*, fail_after=False):
        def verify_after():
            stage.verify_final_schema(connection)
            if fail_after:
                raise stage.SupportBoundaryError("synthetic_postcondition_failure")

        return stage.apply_support_stage(
            acquire_lock=lambda: Command()._migration_lock(
                timeout_seconds=30, allow_non_postgresql=False,
            ),
            verify_identity=verify_identity,
            read_plan=read_plan,
            migrate_support=migrate_support,
            verify_ddl=lambda: stage.verify_ddl_authority(connection),
            verify_after=verify_after,
            atomic=transaction.atomic,
        )

    try:
        executor.migrate(previous_targets)
        historical = MigrationExecutor(connection).loader.project_state(
            [("support", "0001_initial")],
        ).apps.get_model("support", "SupportTicket")
        old_record = historical.objects.create(
            school_id=uuid.uuid4(), title="Synthetic pre-stage ticket",
            description="No private records", priority="medium",
        )
        tables_before = set(connection.introspection.table_names())
        records_before = set(MigrationRecorder(connection).applied_migrations())
        expected_pending = [stage.INQUIRY, stage.LEGACY, stage.SUPPORT_2, stage.SUPPORT_3]
        assert stage.validate_plan(read_plan()) == expected_pending

        with pytest.raises(stage.SupportBoundaryError, match="synthetic_postcondition_failure"):
            execute(fail_after=True)
        assert set(connection.introspection.table_names()) == tables_before
        assert set(MigrationRecorder(connection).applied_migrations()) == records_before
        assert historical.objects.get(pk=old_record.pk).title == "Synthetic pre-stage ticket"
        assert stage.validate_plan(read_plan()) == expected_pending

        barrier = Barrier(2)

        def competing_stage(_index):
            close_old_connections()
            try:
                barrier.wait(timeout=20)
                return execute()
            finally:
                connections.close_all()

        commands.clear()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(competing_stage, (1, 2)))
        expected_applied = [".".join(item) for item in (stage.SUPPORT_2, stage.SUPPORT_3)]
        remaining_names = [".".join(item) for item in (stage.INQUIRY, stage.LEGACY)]
        assert sorted(outcomes, key=lambda item: len(item["applied"])) == [
            {"applied": [], "remaining": remaining_names},
            {"applied": expected_applied, "remaining": remaining_names},
        ]
        assert commands == ["support-only"]
        assert stage.validate_plan(read_plan()) == [stage.INQUIRY, stage.LEGACY]
        applied = MigrationRecorder(connection).applied_migrations()
        assert stage.INQUIRY not in applied
        assert stage.LEGACY not in applied
        stage.verify_final_schema(connection)

        # The still-running pre-stage model omits both new ticket fields.
        inserted = historical.objects.create(
            school_id=uuid.uuid4(), title="Synthetic old-image write",
            description="No private records", priority="low",
        )
        saved = SupportTicket.objects.get(pk=inserted.pk)
        assert saved.requester_id is None
        assert saved.resolution_summary == ""
        assert not saved.events.exists()
        assert execute() == {"applied": [], "remaining": remaining_names}
        assert commands == ["support-only"]
    finally:
        # This guard permits schema restoration only in the disposable test DB.
        MigrationExecutor(connection).migrate(final_targets)
