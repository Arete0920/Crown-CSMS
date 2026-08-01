from datetime import date, datetime, timezone
from types import SimpleNamespace

from governance import services


def test_packet_payload_from_snapshot_returns_payload_or_empty():
    packet = SimpleNamespace(
        snapshots=SimpleNamespace(
            order_by=lambda *_args: SimpleNamespace(
                first=lambda: SimpleNamespace(payload={"sections": {"finance": {"ok": True}}})
            )
        )
    )
    assert services._packet_payload_from_snapshot(packet) == {
        "sections": {"finance": {"ok": True}}
    }

    packet.snapshots = SimpleNamespace(
        order_by=lambda *_args: SimpleNamespace(first=lambda: None)
    )
    assert services._packet_payload_from_snapshot(packet) == {}


def test_serialize_board_packet_normalizes_dates_documents_and_sections(monkeypatch):
    monkeypatch.setattr(
        services,
        "_packet_payload_from_snapshot",
        lambda _packet: {"sections": {"agenda": {"items": [1]}}},
    )
    packet = SimpleNamespace(
        pk=44,
        title="August Board Packet",
        meeting_date=date(2026, 8, 15),
        description="Live governance packet",
        created_at=datetime(2026, 8, 1, 11, 0, tzinfo=timezone.utc),
        documents=({"kind": "pdf"},),
    )

    assert services.serialize_board_packet(packet) == {
        "id": 44,
        "title": "August Board Packet",
        "meeting_date": "2026-08-15",
        "description": "Live governance packet",
        "created_at": "2026-08-01T11:00:00+00:00",
        "documents": [{"kind": "pdf"}],
        "generated_from_live_data": True,
        "sections": {"agenda": {"items": [1]}},
    }


def test_list_board_packets_orders_limits_and_serializes(monkeypatch):
    packets = [SimpleNamespace(pk=2), SimpleNamespace(pk=1)]
    captured = {}

    class Query:
        def order_by(self, *fields):
            captured["order_by"] = fields
            return self

        def __getitem__(self, item):
            captured["slice"] = item
            return packets

    manager = SimpleNamespace(
        filter=lambda **kwargs: captured.update(filter=kwargs) or Query()
    )
    monkeypatch.setattr(services.BoardPacket, "objects", manager)
    monkeypatch.setattr(
        services,
        "serialize_board_packet",
        lambda packet: {"id": packet.pk},
    )

    assert services.list_board_packets(17) == [{"id": 2}, {"id": 1}]
    assert captured["filter"] == {"school_id": 17}
    assert captured["order_by"] == ("-meeting_date", "-created_at")
    assert captured["slice"] == slice(None, 20, None)


def test_build_board_pack_payload_composes_live_sections(monkeypatch):
    meeting_date = date(2026, 8, 20)
    dashboard = {
        "crown_compass": {
            "overall_score": 84,
            "highlights": ["Enrollment stable"],
            "watchlist": ["One audit item"],
        },
        "enrollment": {"current_enrollment": 360},
        "finance": {"tuition_collection_rate": 0.91},
        "attendance": {"avg_daily_attendance": 96.4},
        "discipline": {"open_incidents": 2},
    }
    metrics = {
        "mission": {
            "service_hours_ytd": 420,
            "chapel_attendance_pct": 93.5,
            "survey_pulse_avg": 4.6,
        },
        "compliance": {"required_checks_passing": 5, "required_checks_total": 5},
    }
    delivery = {"channels": [{"channel": "portal", "status": "ready"}]}

    monkeypatch.setattr(services, "build_board_dashboard_payload", lambda **_kwargs: dashboard)
    monkeypatch.setattr(services, "build_board_metrics_payload", lambda **_kwargs: metrics)
    monkeypatch.setattr(
        services,
        "_school",
        lambda _school_id: SimpleNamespace(id=17, name="Heritage Christian Academy"),
    )
    monkeypatch.setattr(
        services,
        "_build_board_agenda_items",
        lambda **_kwargs: [{"topic": "Institutional health review"}],
    )
    monkeypatch.setattr(
        services,
        "build_board_delivery_channels",
        lambda *_args, **_kwargs: delivery,
    )
    monkeypatch.setattr(
        services.timezone,
        "now",
        lambda: datetime(2026, 8, 1, 11, 5, tzinfo=timezone.utc),
    )

    payload = services.build_board_pack_payload(
        17,
        meeting_date=meeting_date,
        title="August Governance Review",
    )

    assert payload["title"] == "August Governance Review"
    assert payload["meeting_date"] == "2026-08-20"
    assert payload["generated_at"] == "2026-08-01T11:05:00+00:00"
    assert payload["school_id"] == "17"
    assert payload["school_name"] == "Heritage Christian Academy"
    assert payload["generated_from_live_data"] is True
    assert payload["sections"]["executive_summary"]["overall_score"] == 84
    assert payload["sections"]["mission"]["service_hours_ytd"] == 420
    assert payload["sections"]["agenda"] == {
        "items": [{"topic": "Institutional health review"}],
        "delivery": delivery,
    }
    assert len(payload["sections"]["document_library"]["documents"]) == 3


def test_build_heritage_verification_payload_reports_live_readiness(monkeypatch):
    metrics = {
        "meta": {"source": "live_db"},
        "enrollment": {"current": 360},
        "finance_health": {"collection_pct": 91.0},
        "mission": {"service_hours_ytd": 420},
    }
    dashboard = {
        "meta": {"source": "live_db"},
        "crown_compass": {"overall_score": 84},
    }
    packets = [{"id": 1}, {"id": 2}]

    monkeypatch.setattr(services, "build_board_metrics_payload", lambda **_kwargs: metrics)
    monkeypatch.setattr(services, "build_board_dashboard_payload", lambda **_kwargs: dashboard)
    monkeypatch.setattr(services, "list_board_packets", lambda _school_id: packets)
    monkeypatch.setattr(
        services.timezone,
        "now",
        lambda: datetime(2026, 8, 1, 11, 10, tzinfo=timezone.utc),
    )

    payload = services.build_heritage_verification_payload(17)

    assert payload["school_name"] == "Heritage Christian Academy"
    assert payload["school_id"] == "17"
    assert payload["status"] == "ready"
    assert payload["generated_at"] == "2026-08-01T11:10:00+00:00"
    assert payload["no_mock_board_metrics"] is True
    assert payload["no_placeholder_board_packs"] is True
    assert payload["board_packets_available"] == 2
    assert payload["snapshot"] == {
        "overall_score": 84,
        "enrollment_current": 360,
        "collection_pct": 91.0,
        "service_hours_ytd": 420,
    }
