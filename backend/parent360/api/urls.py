from django.urls import path

from .secure_views import ParentSelfOverview

urlpatterns = [
    path("me/overview/", ParentSelfOverview.as_view(), name="parent_360_self"),
]
