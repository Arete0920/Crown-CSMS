"""Rehearse the observed DEV migration pair only in an isolated CI database."""

from pathlib import Path

import pytest
from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder


@pytest.mark.django_db(transaction=True)
def test_reviewed_pair_inspection_application_and_legacy_insert(monkeypatch, settings):
    """Real PostgreSQL locks, migrations, constraints and old-image writes work."""
    if connection.vendor != "postgresql":
        pytest.skip("Real PostgreSQL proof runs in the existing survey-postgresql job")
    assert connection.settings_dict["HOST"] in {"localhost", "127.0.0.1"}
    assert str(connection.settings_dict["NAME"]).startswith("test_")

    root = Path(__file__).resolve().parents[3]
    monkeypatch.syspath_prepend(str(root / "scripts" / "ops"))
    import reviewed_legacy_refresh_migrations as boundary
    import run_dev_inquiry_migration as runner
    from core.management.commands.migrate_with_lock import Command
    from core.models import School
    from crm_marketing.models import MarketingLead

    settings.CROWN_SIMPLEJWT_BLACKLIST_ENABLED = False
    settings.CROWN_LEGACY_REFRESH_ONE_USE_ENABLED = False
    boundary.verify_source(root)
    executor = MigrationExecutor(connection)
    final_targets = executor.loader.graph.leaf_nodes()
    previous_targets = [
        ("crm_marketing", "0001_initial"),
        ("crown_api", "0013_attendance_section"),
    ]

    def read_plan():
        current = MigrationExecutor(connection)
        current.loader.check_consistent_history(connection)
        boundary.preflight(connection, current.loader)
        return current.migration_plan(current.loader.graph.leaf_nodes())

    def verify_identity():
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database(), current_schema()")
            assert cursor.fetchone() == (connection.settings_dict["NAME"], "public")

    commands = []

    def invoke(name, **kwargs):
        commands.append((name, kwargs))
        call_command(name, **kwargs, verbosity=0)

    def execute(*, inspect=False):
        return runner.apply_reviewed_plan(
            acquire_lock=lambda: Command()._migration_lock(
                timeout_seconds=5, allow_non_postgresql=False,
            ),
            verify_identity=verify_identity,
            verify_ddl=lambda pending: runner.verify_ddl_authority(
                connection, pending, legacy_stage=True,
            ),
            read_plan=read_plan,
            invoke=invoke,
            check_only=inspect,
            plan_validator=runner.validate_legacy_plan,
            post_verify=None if inspect else lambda: boundary.verify_applied_schema(connection),
        )

    try:
        executor.migrate(previous_targets)
        expected = [".".join(identity) for identity in (boundary.INQUIRY, boundary.REVIEWED)]
        tables_before = set(connection.introspection.table_names())
        records_before = set(MigrationRecorder(connection).applied_migrations())

        assert execute(inspect=True) == expected
        assert commands == []
        assert set(connection.introspection.table_names()) == tables_before
        assert set(MigrationRecorder(connection).applied_migrations()) == records_before

        assert execute() == expected
        boundary.verify_applied_schema(connection)
        assert read_plan() == []
        assert {boundary.INQUIRY, boundary.REVIEWED}.issubset(
            MigrationRecorder(connection).applied_migrations()
        )

        # The still-running older image omits every new inquiry column.
        # Database defaults must let that historical model keep inserting.
        historical_apps = MigrationExecutor(connection).loader.project_state(
            [("crm_marketing", "0001_initial")],
        ).apps
        old_lead = historical_apps.get_model("crm_marketing", "MarketingLead")
        school = School.objects.create(name="Synthetic Migration Pair School")
        inserted = old_lead.objects.create(school_id=school.id, first_source="legacy")
        saved = MarketingLead.objects.get(pk=inserted.pk)
        assert saved.attribution_json == {}
        assert saved.submission_receipt == {}
        assert saved.email == ""
        assert saved.follow_up_consent is False
        assert saved.response_consent is False

        commands.clear()
        assert execute() == []
        assert commands == [
            ("migrate_with_lock", {"lock_timeout_seconds": 300, "check": True}),
            ("migrate", {"check": True, "interactive": False}),
        ]
        assert settings.CROWN_SIMPLEJWT_BLACKLIST_ENABLED is False
        assert settings.CROWN_LEGACY_REFRESH_ONE_USE_ENABLED is False
    finally:
        # Restore only this disposable test database, including on assertion failure.
        MigrationExecutor(connection).migrate(final_targets)
