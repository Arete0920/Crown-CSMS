from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import ClassroomViewSet

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"classrooms", ClassroomViewSet, basename="classroom")

urlpatterns = router.urls

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
