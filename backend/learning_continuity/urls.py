from django.urls import path

from .views import learning_continuity_page

urlpatterns = [
    path("pages/<str:page_key>/", learning_continuity_page, name="learning-continuity-page"),
]
