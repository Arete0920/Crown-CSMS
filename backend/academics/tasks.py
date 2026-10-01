"""Recurring preparation of deduplicated classroom notices."""
from celery import shared_task
from .family_notifications import prepare_digests, prepare_conference_reminders


@shared_task(name='academics.tasks.prepare_family_notices')
def prepare_family_notices():
    return {'digests': prepare_digests(), 'conference_reminders': prepare_conference_reminders()}
