#!/usr/bin/env python
import os
import logging
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
django.setup()

from applications.models import ApplicationEvent
from django.db.models import Count

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

logger.info("=== TOP EVENT TYPES ===")
qs = ApplicationEvent.objects.values("event_type").annotate(n=Count("id")).order_by("-n")[:50]
for r in qs:
    logger.info("  %s: %s", r["event_type"], r["n"])

logger.info("\nTOTAL EVENTS: %s", ApplicationEvent.objects.count())

logger.info("\n=== SAMPLE EVENT PAYLOAD SHAPE ===")
e = ApplicationEvent.objects.exclude(payload__isnull=True).first()
if e:
    payload_is_object = isinstance(e.payload, dict)
    payload_key_count = len(e.payload) if payload_is_object else 0
    logger.info("Event type: %s", e.event_type)
    logger.info("Payload object: %s", payload_is_object)
    logger.info("Payload key count: %s", payload_key_count)
    logger.info("Payload keys: [redacted]")
else:
    logger.info("No events with payload found")
