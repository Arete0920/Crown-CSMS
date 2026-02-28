"""
Platform Operations URL configuration.

All routes are mounted under /api/platform/ in crown_api/urls.py.

  POST /api/platform/schools                — platform_create_school
  GET  /api/platform/schools/list           — platform_list_schools
  GET  /api/platform/provisioning/<job_id>  — platform_provisioning_status
"""
from django.urls import path

from platform_ops import views

urlpatterns = [
    path("schools", views.platform_create_school, name="platform_create_school"),
    path("schools/list", views.platform_list_schools, name="platform_list_schools"),
    path(
        "provisioning/<uuid:job_id>",
        views.platform_provisioning_status,
        name="platform_provisioning_status",
    ),
]
