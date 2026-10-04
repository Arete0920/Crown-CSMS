"""
URL routing for Aid Director APIs

Provides persona-specific API endpoints:
- /api/aid/priority-queue/
- /api/aid/metrics/
- /api/aid/timeline/

Phase 7.5 admin + family endpoints:
- /api/aid/admin/overview/
- /api/aid/admin/recommend-award/
- /api/aid/admin/awards/<award_id>/approve/
- /api/aid/family/status/
"""

from django.urls import path
from . import api_views

urlpatterns = [
    # Existing director persona endpoints
    path("priority-queue/", api_views.aid_priority_queue, name="aid_priority_queue"),
    path("metrics/", api_views.aid_metrics, name="aid_metrics"),
    path("timeline/", api_views.aid_timeline, name="aid_timeline"),

    # Phase 7.5: Admin (award engine + approval)
    path("admin/overview/", api_views.admin_aid_overview, name="aid_admin_overview"),
    path("admin/recommend-award/", api_views.admin_recommend_award, name="aid_admin_recommend_award"),
    path("admin/awards/<int:award_id>/approve/", api_views.admin_approve_award, name="aid_admin_approve_award"),
    path("admin/applications/<int:application_id>/review/", api_views.admin_application_review, name="aid_admin_application_review"),
    path("admin/financial-profiles/carry-forward/", api_views.admin_carry_forward_profile, name="aid_admin_profile_carry_forward"),

    # Phase 7.5: Family portal
    path("family/status/", api_views.family_aid_status, name="aid_family_status"),
]
