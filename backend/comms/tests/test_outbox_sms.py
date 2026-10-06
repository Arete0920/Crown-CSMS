from types import SimpleNamespace

import pytest

from comms import sms_service, tasks


def test_durable_sms_outbox_uses_provider_delivery(monkeypatch):
    sent = {}

    def fake_send_sms_to_number(to_number, message):
        sent["to"] = to_number
        sent["message"] = message
        return "SM-test"

    monkeypatch.setattr(sms_service, "send_sms_to_number", fake_send_sms_to_number)

    tasks._send(
        SimpleNamespace(
            channel="SMS",
            to="+15551234567",
            body="Admissions update",
            subject="",
        )
    )

    assert sent == {"to": "+15551234567", "message": "Admissions update"}


def test_sms_provider_path_fails_closed_when_disabled(monkeypatch):
    monkeypatch.delenv("COMMS_SMS_ENABLED", raising=False)

    with pytest.raises(RuntimeError, match="SMS delivery is disabled"):
        sms_service.send_sms_to_number("+15551234567", "Hello")


def test_sms_provider_path_requires_complete_configuration(monkeypatch):
    monkeypatch.setenv("COMMS_SMS_ENABLED", "true")
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_PHONE_NUMBER", raising=False)

    with pytest.raises(RuntimeError, match="configuration is incomplete"):
        sms_service.send_sms_to_number("+15551234567", "Hello")


def test_push_outbox_remains_explicitly_disabled():
    with pytest.raises(NotImplementedError, match="not an enabled CROWN channel"):
        tasks._send(
            SimpleNamespace(
                channel="PUSH",
                to="device",
                body="Hello",
                subject="",
            )
        )
