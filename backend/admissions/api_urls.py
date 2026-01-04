"""
URL routing for Admissions Director APIs

Provides persona-specific API endpoints:
- /api/admissions/priority-queue/
- /api/admissions/metrics/
- /api/admissions/timeline/
"""

from django.urls import path
from . import api_views

urlpatterns = [
    path("priority-queue/", api_views.admissions_priority_queue, name="admissions_priority_queue"),
    path("metrics/", api_views.admissions_metrics, name="admissions_metrics"),
    path("timeline/", api_views.admissions_timeline, name="admissions_timeline"),
]
