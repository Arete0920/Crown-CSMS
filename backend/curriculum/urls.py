from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CurriculumCourseViewSet

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"courses", CurriculumCourseViewSet, basename="curriculum-course")

urlpatterns = [
    path("", include(router.urls)),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
