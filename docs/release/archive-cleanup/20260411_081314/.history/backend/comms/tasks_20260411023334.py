"""
Celery tasks for Crown2026 communications.

The outbox drain task runs every 10 seconds (see settings.CELERY_BEAT_SCHEDULE)
and sends up to 25 messages per tick using exponential backoff on failure.
"""
from __future__ import annotations

import json
import logging

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .outbox import OutboxMessage

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 10


def _parse_teams_target(raw_target: str) -> tuple[str, str]:
    """Extract team/channel identifiers from JSON or a simple delimited string."""
    value = (raw_target or "").strip()
    if not value:
        raise ValueError("TEAMS outbox target is empty")

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        team_id = str(payload.get("team_id") or payload.get("team") or "").strip()
        channel_id = str(payload.get("channel_id") or payload.get("channel") or "").strip()
        if team_id and channel_id:
            return team_id, channel_id

    for separator in ("|", ":", "/"):
        if separator in value:
            team_id, channel_id = [part.strip() for part in value.split(separator, 1)]
            if team_id and channel_id:
                return team_id, channel_id

    raise ValueError("TEAMS outbox target must include both team_id and channel_id")


def _backoff_seconds(attempts: int) -> int:
    """Exponential backoff: 1, 2, 4, ... capped at 3600s."""
    return min(3600, 2 ** min(attempts, 12))


def _send(msg: OutboxMessage) -> None:
    """Dispatch a single outbox message to the appropriate channel."""
    channel = (msg.channel or "").upper()

    if channel == "EMAIL":
        from django.conf import settings as django_settings  # noqa: PLC0415
        from integrations.graph_client import send_mail      # noqa: PLC0415

        from_user = getattr(django_settings, "GRAPH_FROM_USER", "")
        if not from_user:
            raise ValueError(
                "GRAPH_FROM_USER is not configured. "
                "Set the GRAPH_FROM_USER environment variable to the sender UPN "
                "(e.g. no-reply@yourdomain.com) before starting the Celery worker."
            )
        send_mail(from_user=from_user, to=msg.to, subject=msg.subject, body_html=msg.body)
    elif channel == "TEAMS":
        from comms.teams_service import post_to_teams_channel  # noqa: PLC0415

        team_id, channel_id = _parse_teams_target(msg.to)
        post_to_teams_channel(None, team_id, channel_id, msg.body)
    elif channel in ("SMS", "PUSH"):
        # Phase B: wire additional channel handlers here
        raise NotImplementedError(f"Channel {msg.channel!r} not yet implemented")
    else:
        raise ValueError(f"Unknown channel: {msg.channel!r}")


@shared_task(bind=True, name="comms.tasks.drain_outbox")
def drain_outbox(self, batch_size: int = 25) -> dict:
    """
    Drain up to `batch_size` pending outbox messages.
    Uses SELECT FOR UPDATE SKIP LOCKED so multiple workers are safe.
    """
    now = timezone.now()
    sent = failed = dead = 0

    with transaction.atomic():
        batch = list(
            OutboxMessage.objects
            .select_for_update(skip_locked=True)
            .filter(status=OutboxMessage.STATUS_PENDING, next_attempt_at__lte=now)
            .order_by("next_attempt_at")[:batch_size]
        )

    for msg in batch:
        try:
            msg.attempts += 1
            msg.save(update_fields=["attempts"])

            _send(msg)

            msg.status   = OutboxMessage.STATUS_SENT
            msg.sent_at  = timezone.now()
            msg.last_error = ""
            msg.save(update_fields=["status", "sent_at", "last_error"])
            sent += 1

        except Exception as exc:  # noqa: BLE001
            msg.last_error = str(exc)[:1000]
            if msg.attempts >= MAX_ATTEMPTS:
                msg.status = OutboxMessage.STATUS_DEAD
                msg.save(update_fields=["status", "last_error"])
                dead += 1
                logger.error("OutboxMessage %s moved to DEAD after %d attempts: %s", msg.id, msg.attempts, exc)
            else:
                delay = _backoff_seconds(msg.attempts)
                msg.next_attempt_at = timezone.now() + timezone.timedelta(seconds=delay)
                msg.save(update_fields=["last_error", "next_attempt_at"])
                failed += 1
                logger.warning("OutboxMessage %s failed (attempt %d), retry in %ds: %s", msg.id, msg.attempts, delay, exc)

    return {"sent": sent, "failed": failed, "dead": dead}
