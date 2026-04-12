# curricula/urls.py
from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views

router = SimpleRouter()
router.include_format_suffixes = False
router.register(r'maps', views.CurriculumMapViewSet, basename='curriculum-map')
router.register(r'units', views.UnitViewSet, basename='curriculum-unit')
router.register(r'lessons', views.LessonViewSet, basename='curriculum-lesson')

urlpatterns = router.urls
