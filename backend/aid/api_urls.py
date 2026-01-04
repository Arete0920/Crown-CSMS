"""
URL routing for Aid Director APIs

Provides persona-specific API endpoints:
- /api/aid/priority-queue/
- /api/aid/metrics/
- /api/aid/timeline/
"""

from django.urls import path
from . import api_views

urlpatterns = [
    path("priority-queue/", api_views.aid_priority_queue, name="aid_priority_queue"),
    path("metrics/", api_views.aid_metrics, name="aid_metrics"),
    path("timeline/", api_views.aid_timeline, name="aid_timeline"),
]
