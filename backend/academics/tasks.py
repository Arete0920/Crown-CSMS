"""Scheduled in-app classroom notices; delivery preferences remain authoritative."""
from celery import shared_task
from .family_notifications import prepare_digests, prepare_conference_reminders


@shared_task(name='academics.tasks.prepare_classroom_notices')
def prepare_classroom_notices():
    return {'source':'live', 'delivery':'in_app', 'digest_notices':prepare_digests(),
            'conference_reminders':prepare_conference_reminders()}
