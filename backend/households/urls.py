from rest_framework.routers import DefaultRouter
from .views import GuardianViewSet, HouseholdViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"households", HouseholdViewSet, basename="household")
router.register(r"guardians", GuardianViewSet, basename="guardian")
router.register(r"students", StudentViewSet, basename="student")

urlpatterns = router.urls
