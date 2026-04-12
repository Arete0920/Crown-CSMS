import uuid

import pandas as pd
import pytest

from analytics.predictors import run_retention_risk
from core.models import School
from governance.services import refresh_crown_compass_metric
from onboarding.models_tasks import HelpArticle


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

    compass_payload = refresh_crown_compass_metric(school.id)
    assert compass_payload["predictive_insight"]["model_name"] == "Student Retention Risk"
    assert "top_features" in compass_payload["predictive_insight"]
