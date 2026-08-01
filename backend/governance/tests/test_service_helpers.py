from datetime import date, datetime, timezone
from types import SimpleNamespace

from governance import services


def test_money_ratio_percent_and_clamp_boundaries():
    assert services._money(None) == 0.0
    assert services._money("") == 0.0
    assert services._money(False) == 0.0
    assert services._money("12.345") == 12.35
    assert services._money(object()) == 0.0

    assert services._ratio(1, 0) == 0.0
    assert services._ratio(1, 3) == 0.3333
    assert services._ratio(1, 3, digits=2) == 0.33

    assert services._percent(1, 0) == 0.0
    assert services._percent(1, 4) == 25.0
    assert services._percent(1, 3, digits=2) == 33.33

    assert services._clamp(-3.4) == 0
    assert services._clamp(49.6) == 50
    assert services._clamp(104.2) == 100
    assert services._clamp(7.6, lo=5, hi=8) == 8


def test_service_summary_returns_isolated_fallback_metrics():
    defaults = {"open": 2}

    result = services._service_summary(
        None,
        None,
        school=SimpleNamespace(id=17),
        default_metrics=defaults,
    )

    assert result == {"source": "fallback", "metrics": {"open": 2}}
    assert result["metrics"] is not defaults


def test_service_summary_builds_filters_and_returns_service_summary():
    captured = {}

    class Filters:
        def __init__(self, **kwargs):
            captured["filters"] = kwargs

    class Service:
        def __init__(self, filters):
            captured["service_filter"] = filters

        def summary(self):
            return {"source": "live", "metrics": {"count": 3}}

    result = services._service_summary(
        Service,
        Filters,
        school=SimpleNamespace(id=42),
        default_metrics={},
        date_from=date(2026, 1, 1),
    )

    assert captured["filters"] == {
        "school_id": "42",
        "date_from": date(2026, 1, 1),
    }
    assert captured["service_filter"].__class__ is Filters
    assert result == {"source": "live", "metrics": {"count": 3}}


def test_latest_predictive_insight_returns_empty_without_a_run(monkeypatch):
    manager = SimpleNamespace(
        filter=lambda **kwargs: SimpleNamespace(
            order_by=lambda *_args: SimpleNamespace(first=lambda: None)
        )
    )
    monkeypatch.setattr(services.PredictiveModelRun, "objects", manager)

    assert services._latest_predictive_insight(SimpleNamespace(id=9)) == {}


def test_latest_predictive_insight_normalizes_model_output(monkeypatch):
    run = SimpleNamespace(
        model_name="retention-risk",
        run_date=datetime(2026, 7, 31, 12, 30, tzinfo=timezone.utc),
        output_json={
            "high_risk_count": "4",
            "next_year_total": 355,
            "global_feature_importance": [
                {"feature": "attendance"},
                {"feature": None},
                {"feature": "billing"},
                {"feature": "discipline"},
            ],
            "recommended_actions": ("Call families", "Review aid"),
            "solomon_article_slug": "retention-response",
        },
    )
    manager = SimpleNamespace(
        filter=lambda **kwargs: SimpleNamespace(
            order_by=lambda *_args: SimpleNamespace(first=lambda: run)
        )
    )
    monkeypatch.setattr(services.PredictiveModelRun, "objects", manager)

    result = services._latest_predictive_insight(SimpleNamespace(id=9))

    assert result == {
        "model_name": "retention-risk",
        "run_date": "2026-07-31T12:30:00+00:00",
        "high_risk_count": 4,
        "next_year_total": 355,
        "top_features": ["attendance", "billing"],
        "recommended_actions": ["Call families", "Review aid"],
        "solomon_article_slug": "retention-response",
    }


def test_build_board_agenda_items_marks_compliance_watch_and_ready():
    dashboard = {
        "finance": {"tuition_collection_rate": 0.87},
        "enrollment": {"current_enrollment": 360, "waitlist_total": 12},
        "crown_compass": {"overall_score": 82, "retention_risk": 14},
    }
    metrics = {
        "finance_health": {"fundraising_progress_pct": 76.5},
        "compliance": {"required_checks_passing": 4, "required_checks_total": 5},
        "mission": {"chapel_attendance_pct": 93.2},
    }

    items = services._build_board_agenda_items(dashboard=dashboard, metrics=metrics)

    assert [item["topic"] for item in items] == [
        "Institutional health review",
        "Finance and fundraising",
        "Enrollment and retention",
        "Compliance and mission engagement",
    ]
    assert items[0]["summary"] == "Overall score 82 with retention risk 14%."
    assert "Collection rate 87.0" in items[1]["summary"]
    assert "360 active students" in items[2]["summary"]
    assert items[3]["status"] == "watch"
    assert "4/5 required checks passing" in items[3]["summary"]

    metrics["compliance"]["required_checks_passing"] = 5
    assert services._build_board_agenda_items(
        dashboard=dashboard,
        metrics=metrics,
    )[3]["status"] == "ready"
