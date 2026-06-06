#!/usr/bin/env python
import os
import logging
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from applications.models import ApplicationEvent
from django.db.models import Count


logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

logger.info("=== TOP EVENT TYPES ===")
qs = ApplicationEvent.objects.values('event_type').annotate(n=Count('id')).order_by('-n')[:50]
for r in qs:
    logger.info("  %s: %s", r['event_type'], r['n'])

logger.info("\nTOTAL EVENTS: %s", ApplicationEvent.objects.count())

logger.info("\n=== SAMPLE EVENT PAYLOAD SHAPE ===")
e = ApplicationEvent.objects.exclude(payload__isnull=True).first()
if e:
    payload = e.payload if isinstance(e.payload, dict) else {}
    logger.info("Event type: %s", e.event_type)
    logger.info("Payload key count: %s", len(payload))
    logger.info("Payload keys: %s", sorted(payload.keys()))
else:
    logger.info("No events with payload found")
