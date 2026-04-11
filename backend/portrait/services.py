from __future__ import annotations


def build_portrait_record_summary(school, limit: int = 8) -> dict:
    """Return a portrait-record summary dict for the given school.

    The portrait app is a stub; no domain models exist yet, so this
    returns safe-zero defaults that match the shape expected by
    ``spiritual_life.services.build_mission_metrics_dashboard``.
    """
    return {
        "average_composite_percentage": None,
        "completion_pct": 0,
        "faith_gate_count": 0,
        "review_queue": [],
        "recent_records": [],
        "top_domains": [],
        "alerts": [],
    }
