from django.urls import path

from .views import ExecutiveSelfOverview

urlpatterns = [
    path("me/overview/", ExecutiveSelfOverview.as_view(), name="executive_360_self"),
]
