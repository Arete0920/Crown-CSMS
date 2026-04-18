from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import GuardianViewSet, HouseholdViewSet, StudentViewSet

router = SimpleRouter()
router.include_format_suffixes = False
router.register(r"households", HouseholdViewSet, basename="household")
router.register(r"guardians", GuardianViewSet, basename="guardian")
router.register(r"students", StudentViewSet, basename="student")

urlpatterns = router.urls
