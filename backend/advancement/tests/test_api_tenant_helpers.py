from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import PermissionDenied

from advancement import api
from advancement import payment_hold_views


def _request(*, school=None):
    return SimpleNamespace(school=school)


def test_require_school_fails_closed_without_tenant_context():
    with pytest.raises(PermissionDenied, match="Tenant context required"):
        api._require_school(_request())


def test_require_school_returns_request_school():
    school = SimpleNamespace(id="school-a")

    assert api._require_school(_request(school=school)) is school


def test_donor_queryset_is_scoped_to_request_school(monkeypatch):
    school = SimpleNamespace(id="school-a")
    expected = object()
    manager = MagicMock()
    manager.filter.return_value = expected
    monkeypatch.setattr(api.Donor, "objects", manager)

    view = api.DonorViewSet()
    view.request = _request(school=school)

    assert view.get_queryset() is expected
    manager.filter.assert_called_once_with(school_id="school-a")


def test_campaign_queryset_is_scoped_to_request_school(monkeypatch):
    school = SimpleNamespace(id="school-b")
    expected = object()
    manager = MagicMock()
    manager.filter.return_value = expected
    monkeypatch.setattr(api.Campaign, "objects", manager)

    view = api.CampaignViewSet()
    view.request = _request(school=school)

    assert view.get_queryset() is expected
    manager.filter.assert_called_once_with(school_id="school-b")


def test_event_queryset_applies_school_scope_before_active_filter(monkeypatch):
    school = SimpleNamespace(id="school-c")
    active_queryset = object()
    school_queryset = MagicMock()
    school_queryset.filter.return_value = active_queryset
    manager = MagicMock()
    manager.filter.return_value = school_queryset
    monkeypatch.setattr(api.Event, "objects", manager)

    view = api.EventViewSet()
    view.request = SimpleNamespace(
        school=school,
        query_params={"active": "true"},
    )

    assert view.get_queryset() is active_queryset
    manager.filter.assert_called_once_with(school_id="school-c")
    school_queryset.filter.assert_called_once_with(active=True)


def test_ticket_queryset_applies_school_scope_before_event_filter(monkeypatch):
    school = SimpleNamespace(id="school-d")
    event_queryset = object()
    related_queryset = MagicMock()
    related_queryset.filter.return_value = event_queryset
    school_queryset = MagicMock()
    school_queryset.select_related.return_value = related_queryset
    manager = MagicMock()
    manager.filter.return_value = school_queryset
    monkeypatch.setattr(api.Ticket, "objects", manager)

    view = api.TicketViewSet()
    view.request = SimpleNamespace(
        school=school,
        query_params={"event_id": "event-9"},
    )

    assert view.get_queryset() is event_queryset
    manager.filter.assert_called_once_with(school_id="school-d")
    school_queryset.select_related.assert_called_once_with("event")
    related_queryset.filter.assert_called_once_with(event_id="event-9")


def test_provider_webhook_is_not_exposed_when_provider_is_unconfigured():
    response = payment_hold_views.provider_webhook_not_configured(_request())

    assert response.status_code == 404
