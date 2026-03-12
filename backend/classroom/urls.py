from rest_framework.routers import DefaultRouter
from .views import ClassroomViewSet

router = DefaultRouter()
router.include_format_suffixes = False
router.register(r"classrooms", ClassroomViewSet, basename="classroom")

urlpatterns = router.urls
