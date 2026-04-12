"""
Outbox enqueue helpers.

Always call inside an atomic transaction so the outbox entry is written
in the same DB transaction as the business operation — guaranteeing that
if the transaction rolls back the message is never queued.

Usage:
    from comms.outbox_service import enqueue_email

    with transaction.atomic():
        # ... your business logic ...
        enqueue_email(
            school_id=str(school_id),
            to=recipient_email,
            subject="Welcome!",
            body="<p>Hello</p>",
        )
"""
from __future__ import annotations

import hashlib
import json

from django.db import transaction
from django.utils import timezone

from .outbox import OutboxMessage


def _make_idempotency_key(school_id: str, channel: str, to: str, subject: str, body: str, salt: str = "v1") -> str:
    raw = f"{salt}|{school_id}|{channel}|{to}|{subject}|{body}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


@transaction.atomic
def enqueue_email(school_id: str, to: str, subject: str, body: str) -> OutboxMessage:
    """Queue an email for delivery via Microsoft Graph."""
    key = _make_idempotency_key(school_id, "EMAIL", to, subject, body)
    msg, _ = OutboxMessage.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "school_id": school_id,
            "channel":   "EMAIL",
            "to":        to,
            "subject":   subject,
            "body":      body,
            "next_attempt_at": timezone.now(),
        },
    )
    return msg


@transaction.atomic
def enqueue_sms(school_id: str, to: str, body: str) -> OutboxMessage:
    """Queue an SMS for delivery."""
    key = _make_idempotency_key(school_id, "SMS", to, "", body)
    msg, _ = OutboxMessage.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "school_id": school_id,
            "channel":   "SMS",
            "to":        to,
            "subject":   "",
            "body":      body,
            "next_attempt_at": timezone.now(),
        },
    )
    return msg


@transaction.atomic
def enqueue_teams(school_id: str, team_id: str, channel_id: str, body: str, subject: str = "") -> OutboxMessage:
    """Queue a Teams channel post for delivery through the outbox."""
    target = json.dumps({"team_id": team_id, "channel_id": channel_id}, sort_keys=True)
    key = _make_idempotency_key(school_id, "TEAMS", target, subject, body)
    msg, _ = OutboxMessage.objects.get_or_create(
        idempotency_key=key,
        defaults={
            "school_id": school_id,
            "channel":   "TEAMS",
            "to":        target,
            "subject":   subject,
            "body":      body,
            "next_attempt_at": timezone.now(),
        },
    )
    return msg
