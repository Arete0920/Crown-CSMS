"""Characterize the existing demo dashboard builders without database writes."""

from __future__ import annotations

import json
from uuid import UUID

import pytest

from crown_api.dashboards.payload_contract import validate_dashboard_payload
from crown_api.dashboards.sample_payloads import (
    attendance_sample_payload,
    release_reliability_sample_payload,
)


def _canonical(payload: dict[str, object]) -> str:
    """Encode with original object and array order for strict comparisons."""
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


@pytest.mark.parametrize(
    ("school_id", "expected_id"),
    [
        ("heritage-demo", "heritage-demo"),
        (" other-school ", " other-school "),
        (UUID("11111111-1111-1111-1111-111111111111"),
         "11111111-1111-1111-1111-111111111111"),
        (None, "None"),
    ],
)
def test_attendance_sample_contract(
    school_id: object, expected_id: str
) -> None:
    """Retain complete ordered static payload and string conversion."""
    expected = {
        "dashboard_key": "attendance",
        "metrics": [
            {"label": "Present Rate Today", "value": "96.1%"},
            {"label": "Absent Students", "value": "14"},
            {"label": "Late Check-Ins", "value": "9"},
            {"label": "Missing Homerooms", "value": "3"},
        ],
        "alerts": [
            {
                "title": "Three homerooms still need final attendance submission",
                "level": "High",
                "secondary": "Attendance office follow-up required.",
            },
            {
                "title": "Grade 10 absentee trend is above weekly threshold",
                "level": "Medium",
                "secondary": "Review with school admin and student care.",
            },
            {
                "title": "Two parent outreach messages bounced",
                "level": "Low",
                "secondary": "Retry communication workflow.",
            },
        ],
        "queue": [
            "Review unsubmitted homeroom attendance",
            "Send parent outreach for chronic absence group",
            "Confirm late-check-in corrections from front office",
            "Publish attendance exception summary",
        ],
        "meta": {
            "school_id": expected_id,
            "served_from": "sample",
            "certification_candidate": "hybrid",
        },
    }
    actual = attendance_sample_payload(school_id)
    assert validate_dashboard_payload(actual) is True
    assert _canonical(actual) == _canonical(expected)


@pytest.mark.parametrize("school_id", ["heritage-demo", "other-school", None])
def test_release_reliability_sample_contract(school_id: object) -> None:
    """Preserve the platform-scoped identifier and entire ordered payload."""
    expected = {
        "dashboard_key": "release-reliability",
        "metrics": [
            {"label": "Deployments This Month", "value": "9"},
            {"label": "Open Production Incidents", "value": "2"},
            {"label": "Failed Checks in Last 24h", "value": "4"},
            {"label": "Release Readiness", "value": "Watch"},
        ],
        "alerts": [
            {
                "title": "Contract gate failed on last main candidate build",
                "level": "High",
                "secondary": "Platform engineering follow-up required.",
            },
            {
                "title": "Two environments are not on expected build SHA",
                "level": "High",
                "secondary": "Verify deployment alignment.",
            },
            {
                "title": "Release proof packet is incomplete for one deploy",
                "level": "Medium",
                "secondary": "Complete evidence before certification.",
            },
        ],
        "queue": [
            "Review failed release gate evidence",
            "Verify environment build SHA alignment",
            "Close open production incident postmortem tasks",
            "Publish release readiness summary",
        ],
        "meta": {
            "school_id": "platform",
            "served_from": "sample",
            "certification_candidate": "hybrid",
        },
    }
    actual = release_reliability_sample_payload(school_id)
    assert validate_dashboard_payload(actual) is True
    assert _canonical(actual) == _canonical(expected)
