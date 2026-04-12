import uuid

import pytest

pd = pytest.importorskip("pandas")

from analytics.predictors import run_retention_risk
from core.models import School
from onboarding.models_tasks import HelpArticle
from signals.models import BoardExecutiveMetric


@pytest.mark.django_db
def test_retention_risk_links_solomon_and_compass():
    school = School.objects.create(name=f"Discernment School {uuid.uuid4().hex[:6]}")

    rows = []
    for i in range(24):
        rows.append(
            {
                "attendance_rate": 0.95 - (i % 6) * 0.08,
                "grades_avg": 3.9 - (i % 5) * 0.35,
                "service_hours": 40 - (i % 7) * 4,
                "retained": 1 if i % 4 != 0 else 0,
            }
        )

    result = run_retention_risk(school, pd.DataFrame(rows))

    assert result["solomon_linked"] is True
    assert result["crown_compass_refreshed"] is True

    article = HelpArticle.objects.get(slug="crown-discernment-retention-risk")
    assert article.published is True
    assert article.module == "analytics"

    metric = BoardExecutiveMetric.objects.get(school=school)
    joined_highlights = " ".join(list(metric.highlights or []) + list(metric.watchlist or []))
    assert "Crown Discernment flagged" in joined_highlights
    assert "discernment drivers" in joined_highlights
