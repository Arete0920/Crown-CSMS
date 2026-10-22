"""Sandbox external provider denial tests (no real messages)."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from sandbox_demo.egress import (
    HERITAGE_SCHOOL_ID, SUPPRESSED_REASON,
    SandboxEgressSuppressed, require_external_egress,
    sandbox_external_egress_blocked,
)


def test_heritage_school_is_always_blocked(settings):
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    assert sandbox_external_egress_blocked(school_id=HERITAGE_SCHOOL_ID)
    assert sandbox_external_egress_blocked(recipient=SimpleNamespace(school_id=HERITAGE_SCHOOL_ID))
    assert sandbox_external_egress_blocked(sender=SimpleNamespace(school_id=HERITAGE_SCHOOL_ID))
    with pytest.raises(SandboxEgressSuppressed, match=SUPPRESSED_REASON):
        require_external_egress("EMAIL", school_id=HERITAGE_SCHOOL_ID)


@pytest.mark.django_db
def test_unscoped_heritage_membership_denies_direct_email(settings, monkeypatch):
    from core.models import School, UserAccount, UserRole
    from core.tenant_models import tenant_context
    from comms import email_service

    for flag in ("CROWN_SANDBOX_OUTBOUND_DISABLED", "CROWN_SANDBOX_EVALUATOR_MODE"):
        setattr(settings, flag, False)
        monkeypatch.delenv(flag, raising=False)
    settings.CROWN_DEMO_SCHOOL_ID = HERITAGE_SCHOOL_ID

    school = School.objects.create(id=HERITAGE_SCHOOL_ID, name="Synthetic Heritage")
    user = UserAccount.objects.create_user(
        username="heritage-egress-member", email="member@example.test",
    )
    assert user.school_id is None
    UserRole.objects.create(user=user, school=school, role_code="PARENT")

    token = Mock(side_effect=AssertionError("No provider token may be acquired"))
    monkeypatch.setattr(email_service, "_get_graph_token", token)
    with tenant_context(None):
        assert sandbox_external_egress_blocked(sender=user)
        receipt = email_service.send_email(user, user, "Synthetic", "No send")
    assert receipt.delivery_status == "suppressed"
    assert receipt.error_message == SUPPRESSED_REASON
    token.assert_not_called()


@pytest.mark.django_db
def test_explicit_other_school_scope_is_not_blocked_by_shared_heritage_role(settings, monkeypatch):
    from core.models import School, UserAccount, UserRole
    from core.tenant_models import tenant_context

    for flag in ("CROWN_SANDBOX_OUTBOUND_DISABLED", "CROWN_SANDBOX_EVALUATOR_MODE"):
        setattr(settings, flag, False)
        monkeypatch.delenv(flag, raising=False)
    settings.CROWN_DEMO_SCHOOL_ID = HERITAGE_SCHOOL_ID
    heritage = School.objects.create(id=HERITAGE_SCHOOL_ID, name="Synthetic Heritage")
    other = School.objects.create(name="Unrelated School")
    user = UserAccount.objects.create_user(
        username="shared-egress-member", email="shared@example.test",
    )
    UserRole.objects.create(user=user, school=heritage, role_code="PARENT")
    UserRole.objects.create(user=user, school=other, role_code="PARENT")
    with tenant_context(None):
        assert sandbox_external_egress_blocked(sender=user)
    with tenant_context(other):
        assert not sandbox_external_egress_blocked(sender=user)


def test_evaluator_host_blocks_unscoped_egress(settings):
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = True
    assert sandbox_external_egress_blocked()
    assert sandbox_external_egress_blocked(school_id="another-school")


def test_evaluator_mode_blocks_even_when_flag_is_false(settings):
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = True
    assert sandbox_external_egress_blocked()


def test_unrelated_school_not_blocked_outside_evaluator(settings):
    from core.tenant_models import tenant_context
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    settings.CROWN_DEMO_SCHOOL_ID = HERITAGE_SCHOOL_ID
    with tenant_context(SimpleNamespace(pk="another-school")):
        assert not sandbox_external_egress_blocked(school_id="another-school")


def test_outbox_blocks_before_provider_import(settings):
    from comms import tasks
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    msg = SimpleNamespace(school_id=HERITAGE_SCHOOL_ID, channel="EMAIL", to="fictional@example.org", subject="", body="")
    with pytest.raises(SandboxEgressSuppressed):
        tasks._send(msg)


def test_graph_mail_does_not_acquire_token(settings, monkeypatch):
    from integrations import graph_client
    from core.tenant_models import tenant_context
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    token = Mock(side_effect=AssertionError("no token"))
    post = Mock(side_effect=AssertionError("no network"))
    monkeypatch.setattr(graph_client, "_get_graph_token", token)
    monkeypatch.setattr(graph_client.requests, "post", post)
    with tenant_context(SimpleNamespace(pk=HERITAGE_SCHOOL_ID)):
        with pytest.raises(SandboxEgressSuppressed):
            graph_client.send_mail("sender@example.org", "recipient@example.org", "test", "text")
    token.assert_not_called()
    post.assert_not_called()


def test_sms_does_not_read_credentials(settings, monkeypatch):
    from comms import sms_service
    from core.tenant_models import tenant_context
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    config = Mock(side_effect=AssertionError("no credentials"))
    monkeypatch.setattr(sms_service, "_sms_config", config)
    with tenant_context(SimpleNamespace(pk=HERITAGE_SCHOOL_ID)):
        with pytest.raises(SandboxEgressSuppressed):
            sms_service.send_sms_to_number("+15550100000", "fictional test")
    config.assert_not_called()


def test_dispatch_no_external_channels(settings, monkeypatch):
    from comms import dispatcher
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    identity = SimpleNamespace(school_id=HERITAGE_SCHOOL_ID)
    inapp, email, sms, teams = Mock(), Mock(), Mock(), Mock()
    for name, obj in [("send_inapp", inapp), ("send_email", email), ("send_sms", sms), ("post_to_teams_channel", teams)]:
        monkeypatch.setattr(dispatcher, name, obj)
    dispatcher.dispatch_message(identity, identity, "fictional", "body")
    inapp.assert_called_once()
    email.assert_not_called()
    sms.assert_not_called()
    teams.assert_not_called()


def test_direct_email_and_teams_receipts_are_suppressed(settings, monkeypatch):
    from comms import email_service, teams_service
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    account = SimpleNamespace(school_id=HERITAGE_SCHOOL_ID)
    create = Mock(side_effect=lambda **kwargs: SimpleNamespace(**kwargs))
    for module in (email_service, teams_service):
        monkeypatch.setattr(module, "MessageLog", SimpleNamespace(objects=SimpleNamespace(create=create)))
        token = Mock(side_effect=AssertionError("no Graph token"))
        monkeypatch.setattr(module, "_get_graph_token", token)
    assert email_service.send_email(account, account, "fictional", "body").delivery_status == "suppressed"
    assert teams_service.post_to_teams_channel(account, "team", "channel", "body").delivery_status == "suppressed"


def test_direct_sms_receipt_suppressed(settings, monkeypatch):
    from comms import sms_service
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    sender = SimpleNamespace(school_id=HERITAGE_SCHOOL_ID)
    recipient = SimpleNamespace(school_id=HERITAGE_SCHOOL_ID, phone_number="+15550100000")
    monkeypatch.setattr(sms_service, "MessageLog", SimpleNamespace(objects=SimpleNamespace(create=lambda **kw: SimpleNamespace(**kw))))
    transport = Mock(side_effect=AssertionError("no SMS"))
    monkeypatch.setattr(sms_service, "send_sms_to_number", transport)
    assert sms_service.send_sms(sender, recipient, "fictional").delivery_status == "suppressed"
    transport.assert_not_called()


def test_legacy_outbox_without_school_attribute(settings, monkeypatch):
    from comms import tasks, sms_service
    from core.tenant_models import tenant_context
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    settings.CROWN_DEMO_SCHOOL_ID = HERITAGE_SCHOOL_ID
    send = Mock(return_value="SM-fixture")
    monkeypatch.setattr(sms_service, "send_sms_to_number", send)
    msg = SimpleNamespace(channel="SMS", to="+15551234567", body="Fixture", subject="")
    with tenant_context(SimpleNamespace(pk="another-school")):
        tasks._send(msg)
    send.assert_called_once_with("+15551234567", "Fixture")



def test_advancement_smtp_outbox_suppressed_before_transport(settings, monkeypatch):
    from advancement import emailer

    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    construct = Mock(side_effect=AssertionError("Django mail must not initialize"))
    monkeypatch.setattr(emailer, "EmailMultiAlternatives", construct)
    row = SimpleNamespace(
        school_id=HERITAGE_SCHOOL_ID,
        attempts=0,
        status="pending",
        sent_at=None,
        last_error="",
        save=Mock(),
    )
    assert emailer.send_outbox_email(row) is False
    assert row.status == "failed"
    assert row.last_error == SUPPRESSED_REASON
    assert row.attempts == 0
    assert row.sent_at is None
    row.save.assert_called_once_with(update_fields=["status", "sent_at", "last_error"])
    construct.assert_not_called()


def test_advancement_smtp_outbox_unrelated_school_still_sends(settings, monkeypatch):
    from advancement import emailer
    from core.tenant_models import tenant_context

    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = False
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    settings.CROWN_DEMO_SCHOOL_ID = HERITAGE_SCHOOL_ID
    message = Mock()
    construct = Mock(return_value=message)
    monkeypatch.setattr(emailer, "EmailMultiAlternatives", construct)
    row = SimpleNamespace(
        school_id="11111111-1111-1111-1111-111111111111",
        attempts=0,
        status="pending",
        sent_at=None,
        last_error="",
        subject="Normal school test",
        body_text="Test",
        to_email="synthetic@example.org",
        body_html="",
        attachments_json=[],
        save=Mock(),
    )
    with tenant_context(SimpleNamespace(pk=row.school_id)):
        assert emailer.send_outbox_email(row) is True
    assert row.status == "sent"
    assert row.attempts == 1
    construct.assert_called_once()
    message.send.assert_called_once_with(fail_silently=False)


@pytest.mark.django_db
def test_outbox_suppression_terminal(settings, monkeypatch):
    from comms.models import OutboxMessage
    from comms.tasks import drain_outbox
    from core.models import School
    from integrations import graph_client
    settings.CROWN_SANDBOX_OUTBOUND_DISABLED = True
    settings.CROWN_SANDBOX_EVALUATOR_MODE = False
    school = School.objects.create(name="Egress Quarantine Test School")
    msg = OutboxMessage.objects.create(
        school_id=str(school.pk), channel="EMAIL", to="fictional@example.org",
        subject="Fixture only", body="No transport", idempotency_key="sandbox-egress-terminal-fixture",
    )
    send = Mock(side_effect=AssertionError("no provider"))
    monkeypatch.setattr(graph_client, "send_mail", send)
    result = drain_outbox.run(batch_size=1)
    msg.refresh_from_db()
    assert result == {"sent": 0, "failed": 0, "dead": 1}
    assert msg.status == OutboxMessage.STATUS_DEAD
    assert msg.last_error == SUPPRESSED_REASON
    assert msg.sent_at is None
    send.assert_not_called()
