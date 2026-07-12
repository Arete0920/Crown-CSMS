import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

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
        assert meta.get("school_id") == "heritage-demo"
        assert meta.get("served_from") == "seed-command"
        assert meta.get("live_certified") is False
        assert meta.get("provenance") == "snapshot"
        assert meta.get("non_live_reason") == "seeded_snapshot"
        assert "certification_candidate" not in meta


@pytest.mark.django_db
@pytest.mark.parametrize("school_id", [None, "", "   "])
def test_seed_dashboard_snapshots_rejects_empty_school_id(school_id):
    with pytest.raises(CommandError, match="non-empty school identifier"):
        call_command("seed_dashboard_snapshots", school_id=school_id)

    assert DashboardSnapshot.objects.count() == 0
