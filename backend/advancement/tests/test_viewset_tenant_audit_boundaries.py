from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from advancement import api


def _request(*, school_id="school-a", query=None, user_id=7):
    raw = APIRequestFactory().get("/api/v1/advancement/", data=query or {})
    request = Request(raw)
    request.school = None if school_id is None else SimpleNamespace(id=school_id)
    request.user = SimpleNamespace(id=user_id, is_authenticated=True)
    return request


def _view(viewset_cls, *, school_id="school-a", query=None):
    view = viewset_cls()
    view.request = _request(school_id=school_id, query=query)
    return view


def _manager_with_filter(monkeypatch, model):
    manager = MagicMock()
    queryset = MagicMock()
    manager.filter.return_value = queryset
    monkeypatch.setattr(model, "objects", manager)
    return manager, queryset


def test_require_school_returns_bound_school():
    request = _request(school_id="school-a")

    assert api._require_school(request) is request.school


def test_require_school_rejects_missing_tenant_context():
    with pytest.raises(PermissionDenied, match="Tenant context required"):
        api._require_school(_request(school_id=None))


@pytest.mark.parametrize(
    ("viewset_cls", "model"),
    (
        (api.DonorViewSet, api.Donor),
        (api.CampaignViewSet, api.Campaign),
        (api.SponsorshipPackageViewSet, api.SponsorshipPackage),
        (api.EventViewSet, api.Event),
        (api.StoreItemViewSet, api.StoreItem),
    ),
)
def test_simple_viewsets_scope_querysets_to_request_school(monkeypatch, viewset_cls, model):
    manager, queryset = _manager_with_filter(monkeypatch, model)

    result = _view(viewset_cls).get_queryset()

    assert result is queryset
    manager.filter.assert_called_once_with(school_id="school-a")


def test_event_queryset_applies_active_filter_only_for_literal_true(monkeypatch):
    manager, queryset = _manager_with_filter(monkeypatch, api.Event)
    active_queryset = MagicMock()
    queryset.filter.return_value = active_queryset

    result = _view(api.EventViewSet, query={"active": "true"}).get_queryset()

    assert result is active_queryset
    manager.filter.assert_called_once_with(school_id="school-a")
    queryset.filter.assert_called_once_with(active=True)


def test_event_queryset_leaves_other_active_values_unfiltered(monkeypatch):
    manager, queryset = _manager_with_filter(monkeypatch, api.Event)

    result = _view(api.EventViewSet, query={"active": "1"}).get_queryset()

    assert result is queryset
    manager.filter.assert_called_once_with(school_id="school-a")
    queryset.filter.assert_not_called()


def test_store_item_queryset_applies_active_filter(monkeypatch):
    manager, queryset = _manager_with_filter(monkeypatch, api.StoreItem)
    active_queryset = MagicMock()
    queryset.filter.return_value = active_queryset

    result = _view(api.StoreItemViewSet, query={"active": "true"}).get_queryset()

    assert result is active_queryset
    manager.filter.assert_called_once_with(school_id="school-a")
    queryset.filter.assert_called_once_with(active=True)


def test_ticket_queryset_scopes_selects_event_and_filters_event_id(monkeypatch):
    manager, queryset = _manager_with_filter(monkeypatch, api.Ticket)
    selected = MagicMock()
    filtered = MagicMock()
    queryset.select_related.return_value = selected
    selected.filter.return_value = filtered

    result = _view(api.TicketViewSet, query={"event_id": "event-a"}).get_queryset()

    assert result is filtered
    manager.filter.assert_called_once_with(school_id="school-a")
    queryset.select_related.assert_called_once_with("event")
    selected.filter.assert_called_once_with(event_id="event-a")


def test_ticket_queryset_without_event_id_returns_selected_queryset(monkeypatch):
    manager, queryset = _manager_with_filter(monkeypatch, api.Ticket)
    selected = MagicMock()
    queryset.select_related.return_value = selected

    result = _view(api.TicketViewSet).get_queryset()

    assert result is selected
    manager.filter.assert_called_once_with(school_id="school-a")
    queryset.select_related.assert_called_once_with("event")
    selected.filter.assert_not_called()


@pytest.mark.parametrize(
    ("viewset_cls", "action", "id_key"),
    (
        (api.DonorViewSet, "advancement.donor.created", "donor_id"),
        (api.CampaignViewSet, "advancement.campaign.created", "campaign_id"),
        (api.SponsorshipPackageViewSet, "advancement.sponsorship.created", "package_id"),
        (api.EventViewSet, "advancement.event.created", "event_id"),
    ),
)
def test_audited_creates_force_school_and_emit_exact_event(
    monkeypatch, viewset_cls, action, id_key
):
    audit = MagicMock()
    monkeypatch.setattr(api, "audit_event", audit)
    serializer = MagicMock()
    serializer.save.return_value = SimpleNamespace(id="object-a")
    view = _view(viewset_cls)

    view.perform_create(serializer)

    serializer.save.assert_called_once_with(school_id="school-a")
    audit.assert_called_once_with(
        action,
        user=view.request.user,
        school=view.request.school,
        extra={id_key: "object-a"},
    )


def test_store_item_create_forces_school_without_inventing_audit_contract(monkeypatch):
    audit = MagicMock()
    monkeypatch.setattr(api, "audit_event", audit)
    serializer = MagicMock()

    _view(api.StoreItemViewSet).perform_create(serializer)

    serializer.save.assert_called_once_with(school_id="school-a")
    audit.assert_not_called()


@pytest.mark.parametrize(
    ("viewset_cls", "action", "id_key"),
    (
        (api.DonorViewSet, "advancement.donor.updated", "donor_id"),
        (api.CampaignViewSet, "advancement.campaign.updated", "campaign_id"),
    ),
)
def test_updates_emit_exact_audit_event(monkeypatch, viewset_cls, action, id_key):
    audit = MagicMock()
    monkeypatch.setattr(api, "audit_event", audit)
    serializer = MagicMock()
    serializer.save.return_value = SimpleNamespace(id="object-a")
    view = _view(viewset_cls)

    view.perform_update(serializer)

    serializer.save.assert_called_once_with()
    audit.assert_called_once_with(
        action,
        user=view.request.user,
        school=view.request.school,
        extra={id_key: "object-a"},
    )


@pytest.mark.parametrize(
    ("viewset_cls", "action", "id_key"),
    (
        (api.DonorViewSet, "advancement.donor.deleted", "donor_id"),
        (api.CampaignViewSet, "advancement.campaign.deleted", "campaign_id"),
    ),
)
def test_deletes_audit_before_delete(monkeypatch, viewset_cls, action, id_key):
    events = []
    instance = SimpleNamespace(id="object-a")
    instance.delete = MagicMock(side_effect=lambda: events.append("delete"))

    def record_audit(*args, **kwargs):
        events.append((args, kwargs))

    monkeypatch.setattr(api, "audit_event", record_audit)
    view = _view(viewset_cls)

    view.perform_destroy(instance)

    assert events == [
        (
            (action,),
            {
                "user": view.request.user,
                "school": view.request.school,
                "extra": {id_key: "object-a"},
            },
        ),
        "delete",
    ]
    instance.delete.assert_called_once_with()


def test_ticket_check_in_returns_conflict_without_save_or_audit(monkeypatch):
    ticket = SimpleNamespace(id="ticket-a", checked_in=True, checked_in_at=None)
    ticket.save = MagicMock()
    audit = MagicMock()
    monkeypatch.setattr(api, "audit_event", audit)
    view = _view(api.TicketViewSet)
    view.get_object = MagicMock(return_value=ticket)

    response = view.check_in(view.request, pk="ticket-a")

    assert response.status_code == 409
    assert response.data == {"detail": "Ticket already checked in."}
    ticket.save.assert_not_called()
    audit.assert_not_called()


def test_ticket_check_in_sets_timestamp_saves_fields_audits_and_serializes(monkeypatch):
    now = datetime(2026, 8, 1, 12, 0, tzinfo=timezone.utc)
    ticket = SimpleNamespace(id="ticket-a", checked_in=False, checked_in_at=None)
    ticket.save = MagicMock()
    audit = MagicMock()
    monkeypatch.setattr(api.timezone, "now", MagicMock(return_value=now))
    monkeypatch.setattr(api, "audit_event", audit)
    view = _view(api.TicketViewSet)
    view.get_object = MagicMock(return_value=ticket)

    response = view.check_in(view.request, pk="ticket-a")

    assert response.status_code == 200
    assert response.data == {"status": "checked_in", "ticket_id": "ticket-a"}
    assert ticket.checked_in is True
    assert ticket.checked_in_at == now
    ticket.save.assert_called_once_with(update_fields=["checked_in", "checked_in_at"])
    audit.assert_called_once_with(
        "advancement.ticket.checkin",
        user=view.request.user,
        school=view.request.school,
        extra={"ticket_id": "ticket-a"},
    )
