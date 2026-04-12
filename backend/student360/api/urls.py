from django.urls import path
from student360.api.views import StudentOverview, StudentSelfOverview

urlpatterns = [
    path("students/<uuid:student_id>/overview/", StudentOverview.as_view(), name="student_360_overview"),
    path("me/overview/", StudentSelfOverview.as_view(), name="student_360_self"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
