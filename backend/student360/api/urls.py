from django.urls import path
from student360.api.scoped_views import ScopedStudentOverview, ScopedStudentSelfOverview

urlpatterns = [
    path("students/<uuid:student_id>/overview/", ScopedStudentOverview.as_view(), name="student_360_overview"),
    path("me/overview/", ScopedStudentSelfOverview.as_view(), name="student_360_self"),
]
