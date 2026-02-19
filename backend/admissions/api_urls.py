"""
URL routing for Admissions Director APIs

Provides persona-specific API endpoints:
- /api/admissions/priority-queue/
- /api/admissions/metrics/
- /api/admissions/timeline/
"""

from django.urls import path
from . import api_views
from .views_admissions_links import (
    admissions_application_detail,
    admissions_applications_list,
)
from .views_enroll import enroll_applicant

urlpatterns = [
    path("priority-queue/", api_views.admissions_priority_queue, name="admissions_priority_queue"),
    path("metrics/", api_views.admissions_metrics, name="admissions_metrics"),
    path("timeline/", api_views.admissions_timeline, name="admissions_timeline"),

    # Enroll action (Lane 1)
    path("enroll/", enroll_applicant, name="admissions_enroll"),

    # Applications linkage (Household/Student spine) - read-only
    path("applications/", admissions_applications_list, name="admissions_applications_list"),
    path(
        "applications/<int:application_id>/",
        admissions_application_detail,
        name="admissions_application_detail",
    ),
]
