from datetime import date

from signals.models import BoardExecutiveMetric
from signals.serializers import BoardExecutiveMetricSerializer


def test_unwired_health_indexes_are_unassessed_and_aftercare_metric_is_preserved():
    metric = BoardExecutiveMetric(
        as_of_date=date(2026, 10, 13),
        enrollment_health=0, financial_health=97, culture_health=0,
        mission_health=100, retention_risk=25,
        highlights=["4 student(s) actively enrolled in aftercare"],
        watchlist=["1 late pickup(s) in the last 30 days"],
    )
    data = BoardExecutiveMetricSerializer(metric).data
    assert all(data[field] is None for field in (
        "enrollment_health", "financial_health", "culture_health", "mission_health",
    ))
    assert data["calculation_status"] == "awaiting_validated_metric_definitions"
    assert data["retention_risk"] == 25
    assert data["highlights"] == metric.highlights
    assert data["watchlist"] == metric.watchlist
