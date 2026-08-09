from __future__ import annotations

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from crown_api.dashboards.models import DashboardSnapshot
from crown_api.management.commands import seed_all_dashboard_snapshots as seed_command
from crown_api.management.commands.seed_all_dashboard_snapshots import (
    ACTIVE_DASHBOARD_PAYLOAD_BUILDERS,
    EXPECTED_ACTIVE_BUILDER_COUNT,
    build_snapshot_payload,
)

TEST_SCHOOL_ID = "19801b59-8c05-4c84-9312-5d792e4e839d"


def run_seed_command(*args):
    output = StringIO()
    call_command("seed_all_dashboard_snapshots", *args, stdout=output)
    return output.getvalue()


def test_active_builder_map_includes_batch5_summer_camp():
    assert len(ACTIVE_DASHBOARD_PAYLOAD_BUILDERS) == EXPECTED_ACTIVE_BUILDER_COUNT
    assert "summer-camp" in ACTIVE_DASHBOARD_PAYLOAD_BUILDERS
    assert "school-administrator" in ACTIVE_DASHBOARD_PAYLOAD_BUILDERS
    assert "billing" in ACTIVE_DASHBOARD_PAYLOAD_BUILDERS
    assert "registrar" in ACTIVE_DASHBOARD_PAYLOAD_BUILDERS
    assert "admissions" in ACTIVE_DASHBOARD_PAYLOAD_BUILDERS


@pytest.mark.django_db
@pytest.mark.parametrize(
    "dashboard_key,builder", sorted(ACTIVE_DASHBOARD_PAYLOAD_BUILDERS.items())
)
def test_all_active_builders_generate_snapshot_payloads(dashboard_key, builder):
    payload = build_snapshot_payload(dashboard_key, builder, TEST_SCHOOL_ID)
    assert payload["dashboard_key"] == dashboard_key
    assert isinstance(payload["metrics"], list)
    assert isinstance(payload["alerts"], list)
    assert isinstance(payload["queue"], list)
    assert isinstance(payload["meta"], dict)
    meta = payload["meta"]
    assert meta["served_from"] == "snapshot"
    assert meta["seeded_by"] == "seed_all_dashboard_snapshots"
    assert meta["seed_source"] == "sample-derived-snapshot"
    assert meta["no_pretend_classification"] == "snapshot"
    assert meta["live_certified"] is False
    assert meta["school_id"] == TEST_SCHOOL_ID
    assert "snapshot_derived_from" in meta


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_rejects_oversized_source():
    source_max_length = DashboardSnapshot._meta.get_field("source").max_length
    assert source_max_length is not None
    with pytest.raises(CommandError, match=f"max_length={source_max_length}"):
        run_seed_command(
            "--school-id",
            TEST_SCHOOL_ID,
            "--source",
            "x" * (source_max_length + 1),
            "--dry-run",
        )
    assert DashboardSnapshot.objects.filter(school_id=TEST_SCHOOL_ID).count() == 0


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_rejects_oversized_notes():
    notes_max_length = DashboardSnapshot._meta.get_field("notes").max_length
    assert notes_max_length is not None
    with pytest.raises(CommandError, match=f"max_length={notes_max_length}"):
        run_seed_command(
            "--school-id",
            TEST_SCHOOL_ID,
            "--notes",
            "x" * (notes_max_length + 1),
            "--dry-run",
        )
    assert DashboardSnapshot.objects.filter(school_id=TEST_SCHOOL_ID).count() == 0


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_builder_failure_writes_no_rows(monkeypatch):
    def failing_builder(_school_id):
        raise RuntimeError("intentional builder failure")

    builders = dict(ACTIVE_DASHBOARD_PAYLOAD_BUILDERS)
    builders["zz-failing-dashboard"] = failing_builder
    monkeypatch.setattr(seed_command, "ACTIVE_DASHBOARD_PAYLOAD_BUILDERS", builders)

    with pytest.raises(CommandError, match="no rows were written"):
        run_seed_command(
            "--school-id",
            TEST_SCHOOL_ID,
            "--allow-count-mismatch",
        )

    assert DashboardSnapshot.objects.filter(school_id=TEST_SCHOOL_ID).count() == 0


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_dry_run_writes_no_rows():
    output = run_seed_command("--school-id", TEST_SCHOOL_ID, "--dry-run")
    assert "active-builders=40" in output
    assert "created=40" in output
    assert "updated=0" in output
    assert "failed=0" in output
    assert DashboardSnapshot.objects.filter(school_id=TEST_SCHOOL_ID).count() == 0


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_creates_all_active_snapshots():
    output = run_seed_command("--school-id", TEST_SCHOOL_ID)
    assert "active-builders=40" in output
    assert "created=40" in output
    assert "failed=0" in output
    snapshots = DashboardSnapshot.objects.filter(school_id=TEST_SCHOOL_ID)
    assert snapshots.count() == EXPECTED_ACTIVE_BUILDER_COUNT
    assert snapshots.filter(dashboard_key="summer-camp").exists()
    sample = snapshots.get(dashboard_key="summer-camp")
    assert sample.source == "sample-derived-snapshot"
    assert "not live data" in sample.notes
    assert sample.payload["meta"]["served_from"] == "snapshot"
    assert sample.payload["meta"]["snapshot_derived_from"] == "sample"
    assert sample.payload["meta"]["live_certified"] is False


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_is_idempotent_without_overwrite():
    run_seed_command("--school-id", TEST_SCHOOL_ID)
    output = run_seed_command("--school-id", TEST_SCHOOL_ID)
    assert "created=0" in output
    assert "updated=0" in output
    assert "skipped-existing=40" in output
    assert "failed=0" in output
    assert (
        DashboardSnapshot.objects.filter(school_id=TEST_SCHOOL_ID).count()
        == EXPECTED_ACTIVE_BUILDER_COUNT
    )


@pytest.mark.django_db
def test_seed_all_dashboard_snapshots_overwrite_updates_existing_rows():
    run_seed_command("--school-id", TEST_SCHOOL_ID)
    DashboardSnapshot.objects.filter(
        school_id=TEST_SCHOOL_ID,
        dashboard_key="summer-camp",
    ).update(source="old-source", notes="old notes")
    output = run_seed_command("--school-id", TEST_SCHOOL_ID, "--overwrite")
    assert "created=0" in output
    assert "updated=40" in output
    assert "failed=0" in output
    summer_camp = DashboardSnapshot.objects.get(
        school_id=TEST_SCHOOL_ID,
        dashboard_key="summer-camp",
    )
    assert summer_camp.source == "sample-derived-snapshot"
    assert "not live data" in summer_camp.notes
