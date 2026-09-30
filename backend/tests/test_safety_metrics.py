from types import SimpleNamespace
from unittest.mock import MagicMock, call

from rest_framework.test import APIRequestFactory, force_authenticate

from safety import api as safety_api


def test_safety_metrics_uses_resolved_state_and_preserves_status_contract(monkeypatch):
    school = SimpleNamespace(id="school-a")
    request = APIRequestFactory().get("/api/v1/safety/metrics/")
    request.school = school
    roles = MagicMock()
    roles.all.return_value.filter.return_value.values_list.return_value = []
    force_authenticate(request, user=SimpleNamespace(is_authenticated=True, roles=roles))
    denied = safety_api.safety_metrics(request)
    assert denied.status_code == 403
    # Isolate aggregation only after proving the public wrapper fails closed.
    monkeypatch.setattr("core.permissions.user_has_permission", lambda user, code, school=None: code == "safety.view" and school is request.school)

    manager = MagicMock()
    queryset = MagicMock()
    manager.filter.return_value = queryset
    monkeypatch.setattr(safety_api.IncidentReport, "objects", manager)

    severity_values = MagicMock()
    severity_annotated = MagicMock()
    severity_ordered = MagicMock()
    queryset.values.return_value = severity_values
    severity_values.annotate.return_value = severity_annotated
    severity_annotated.order_by.return_value = severity_ordered
    severity_ordered.values.return_value = [
        {"severity": "high", "count": 2},
        {"severity": "low", "count": 1},
    ]

    queryset.count.return_value = 3
    open_queryset = MagicMock()
    open_queryset.count.return_value = 2
    closed_queryset = MagicMock()
    closed_queryset.count.return_value = 1

    def filter_by_resolved(**kwargs):
        if kwargs == {"resolved": False}:
            return open_queryset
        if kwargs == {"resolved": True}:
            return closed_queryset
        raise AssertionError(f"Unexpected safety metrics filter: {kwargs}")

    queryset.filter.side_effect = filter_by_resolved

    response = safety_api.safety_metrics(request)

    assert response.status_code == 200
    assert response.data == {
        "total_incidents": 3,
        "open_incidents": 2,
        "closed_incidents": 1,
        "by_severity": [
            {"severity": "high", "count": 2},
            {"severity": "low", "count": 1},
        ],
        "by_status": [
            {"status": "open", "count": 2},
            {"status": "closed", "count": 1},
        ],
    }
    manager.filter.assert_called_once_with(school_id="school-a")
    queryset.values.assert_called_once_with("severity")
    queryset.filter.assert_has_calls(
        [call(resolved=False), call(resolved=True)],
        any_order=True,
    )
