from django.urls import path
from student360.api.views import StudentOverview, StudentSelfOverview

urlpatterns = [
    path("students/<uuid:student_id>/overview/", StudentOverview.as_view(), name="student_360_overview"),
    path("me/overview/", StudentSelfOverview.as_view(), name="student_360_self"),
]
