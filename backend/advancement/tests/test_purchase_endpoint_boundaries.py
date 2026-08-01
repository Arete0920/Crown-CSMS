from types import SimpleNamespace
from unittest.mock import MagicMock

from rest_framework.test import APIRequestFactory, force_authenticate

from advancement import api


def _request(path, payload):
    request = APIRequestFactory().post(path, payload, format="json")
    force_authenticate(
        request,
        user=SimpleNamespace(is_authenticated=True, id=1),
    )
    request.school = SimpleNamespace(id="school-a")
    return request


def _serializer(validated_data):
    serializer = MagicMock()
    serializer.validated_data = validated_data
    serializer.is_valid.return_value = True
    return serializer


def test_purchase_ticket_returns_not_found_for_other_tenant_event(monkeypatch):
    serializer = _serializer(
        {
            "event_id": "event-a",
            "purchaser_name": "Jordan Parent",
            "purchaser_email": "jordan@example.com",
        }
    )
    monkeypatch.setattr(api, "TicketPurchaseSerializer", MagicMock(return_value=serializer))
    event_manager = MagicMock()
    event_manager.get.side_effect = api.Event.DoesNotExist
    monkeypatch.setattr(api.Event, "objects", event_manager)
    service = MagicMock()
    monkeypatch.setattr(api, "create_ticket_purchase", service)

    response = api.purchase_ticket(
        _request(
            "/api/advancement/purchase/ticket/",
            {
                "event_id": "event-a",
                "purchaser_name": "Jordan Parent",
                "purchaser_email": "jordan@example.com",
            },
        )
    )

    assert response.status_code == 404
    assert response.data == {"detail": "Event not found."}
    event_manager.get.assert_called_once_with(pk="event-a", school_id="school-a")
    service.assert_not_called()


def test_purchase_ticket_sanitizes_service_failure(monkeypatch):
    serializer = _serializer(
        {
            "event_id": "event-a",
            "purchaser_name": "Jordan Parent",
            "purchaser_email": "jordan@example.com",
        }
    )
    monkeypatch.setattr(api, "TicketPurchaseSerializer", MagicMock(return_value=serializer))
    event = SimpleNamespace(id="event-a")
    event_manager = MagicMock()
    event_manager.get.return_value = event
    monkeypatch.setattr(api.Event, "objects", event_manager)
    service = MagicMock(side_effect=ValueError("inventory internals"))
    monkeypatch.setattr(api, "create_ticket_purchase", service)
    logger = MagicMock()
    monkeypatch.setattr(api, "logger", logger)

    response = api.purchase_ticket(
        _request(
            "/api/advancement/purchase/ticket/",
            {
                "event_id": "event-a",
                "purchaser_name": "Jordan Parent",
                "purchaser_email": "jordan@example.com",
            },
        )
    )

    assert response.status_code == 400
    assert response.data == {"detail": "Request failed."}
    service.assert_called_once_with(
        school_id="school-a",
        event=event,
        purchaser_name="Jordan Parent",
        purchaser_email="jordan@example.com",
    )
    logger.exception.assert_called_once_with("Ticket purchase failed")


def test_purchase_ticket_serializes_success(monkeypatch):
    serializer = _serializer(
        {
            "event_id": "event-a",
            "purchaser_name": "Jordan Parent",
            "purchaser_email": "jordan@example.com",
        }
    )
    monkeypatch.setattr(api, "TicketPurchaseSerializer", MagicMock(return_value=serializer))
    event = SimpleNamespace(id="event-a")
    event_manager = MagicMock()
    event_manager.get.return_value = event
    monkeypatch.setattr(api.Event, "objects", event_manager)
    ticket = SimpleNamespace(id="ticket-a")
    service = MagicMock(return_value=ticket)
    monkeypatch.setattr(api, "create_ticket_purchase", service)
    output = MagicMock()
    output.data = {"id": "ticket-a", "status": "issued"}
    output_serializer = MagicMock(return_value=output)
    monkeypatch.setattr(api, "TicketSerializer", output_serializer)

    response = api.purchase_ticket(
        _request(
            "/api/advancement/purchase/ticket/",
            {
                "event_id": "event-a",
                "purchaser_name": "Jordan Parent",
                "purchaser_email": "jordan@example.com",
            },
        )
    )

    assert response.status_code == 201
    assert response.data == {"id": "ticket-a", "status": "issued"}
    output_serializer.assert_called_once_with(ticket)


def test_purchase_store_item_returns_not_found_for_other_tenant_item(monkeypatch):
    serializer = _serializer({"item_id": "item-a", "quantity": 2})
    monkeypatch.setattr(api, "StorePurchaseSerializer", MagicMock(return_value=serializer))
    item_manager = MagicMock()
    item_manager.get.side_effect = api.StoreItem.DoesNotExist
    monkeypatch.setattr(api.StoreItem, "objects", item_manager)
    service = MagicMock()
    monkeypatch.setattr(api, "create_store_purchase", service)

    response = api.purchase_store_item(
        _request(
            "/api/advancement/purchase/store/",
            {"item_id": "item-a", "quantity": 2},
        )
    )

    assert response.status_code == 404
    assert response.data == {"detail": "Store item not found."}
    item_manager.get.assert_called_once_with(pk="item-a", school_id="school-a")
    service.assert_not_called()


def test_purchase_store_item_sanitizes_service_failure(monkeypatch):
    serializer = _serializer({"item_id": "item-a", "quantity": 2})
    monkeypatch.setattr(api, "StorePurchaseSerializer", MagicMock(return_value=serializer))
    item = SimpleNamespace(id="item-a")
    item_manager = MagicMock()
    item_manager.get.return_value = item
    monkeypatch.setattr(api.StoreItem, "objects", item_manager)
    service = MagicMock(side_effect=ValueError("stock internals"))
    monkeypatch.setattr(api, "create_store_purchase", service)
    logger = MagicMock()
    monkeypatch.setattr(api, "logger", logger)

    response = api.purchase_store_item(
        _request(
            "/api/advancement/purchase/store/",
            {"item_id": "item-a", "quantity": 2},
        )
    )

    assert response.status_code == 400
    assert response.data == {"detail": "Request failed."}
    service.assert_called_once_with(
        school_id="school-a",
        item=item,
        quantity=2,
    )
    logger.exception.assert_called_once_with("Store purchase failed")


def test_purchase_store_item_serializes_success(monkeypatch):
    serializer = _serializer({"item_id": "item-a", "quantity": 2})
    monkeypatch.setattr(api, "StorePurchaseSerializer", MagicMock(return_value=serializer))
    item = SimpleNamespace(id="item-a")
    item_manager = MagicMock()
    item_manager.get.return_value = item
    monkeypatch.setattr(api.StoreItem, "objects", item_manager)
    transaction = SimpleNamespace(id="txn-a")
    service = MagicMock(return_value=transaction)
    monkeypatch.setattr(api, "create_store_purchase", service)
    output = MagicMock()
    output.data = {"id": "txn-a", "quantity": 2}
    output_serializer = MagicMock(return_value=output)
    monkeypatch.setattr(api, "AdvancementTransactionSerializer", output_serializer)

    response = api.purchase_store_item(
        _request(
            "/api/advancement/purchase/store/",
            {"item_id": "item-a", "quantity": 2},
        )
    )

    assert response.status_code == 201
    assert response.data == {"id": "txn-a", "quantity": 2}
    output_serializer.assert_called_once_with(transaction)
