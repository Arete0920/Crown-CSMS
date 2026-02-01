#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crown_api.settings')
django.setup()

from applications.models import ApplicationEvent
from django.db.models import Count

print("=== TOP EVENT TYPES ===")
qs = ApplicationEvent.objects.values('event_type').annotate(n=Count('id')).order_by('-n')[:50]
for r in qs:
    print(f"  {r['event_type']}: {r['n']}")

print(f"\nTOTAL EVENTS: {ApplicationEvent.objects.count()}")

print("\n=== SAMPLE EVENT WITH PAYLOAD ===")
e = ApplicationEvent.objects.exclude(payload__isnull=True).first()
if e:
    print(f"Event type: {e.event_type}")
    print(f"Payload keys: {sorted(list(e.payload.keys())) if e.payload else 'None'}")
    print(f"Sample payload: {e.payload}")
else:
    print("No events with payload found")
