from django.urls import path
from .views import SectionsList

urlpatterns = [
    path("sections/", SectionsList.as_view()),
]
