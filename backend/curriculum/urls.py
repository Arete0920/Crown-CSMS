from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CurriculumCourseViewSet

router = DefaultRouter()
router.register(r"courses", CurriculumCourseViewSet, basename="curriculum-course")

urlpatterns = [
    path("", include(router.urls)),
]
