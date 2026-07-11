import pytest
from django.core.management import call_command

from crown_api.dashboards.models import DashboardSnapshot


@pytest.mark.django_db
def test_seed_dashboard_snapshots_marks_seeded_records_non_live_by_default():
    call_command("seed_dashboard_snapshots", school_id="heritage-demo")

    attendance = DashboardSnapshot.objects.get(
        school_id="heritage-demo",
        dashboard_key="attendance",
    )
    release = DashboardSnapshot.objects.get(
        school_id="heritage-demo",
        dashboard_key="release-reliability",
    )

    for snapshot in (attendance, release):
        meta = snapshot.payload.get("meta", {})
        assert meta.get("served_from") == "seed-command"
        assert meta.get("live_certified") is False
        assert meta.get("provenance") == "snapshot"
        assert meta.get("non_live_reason") == "seeded_snapshot"
        assert "certification_candidate" not in meta
