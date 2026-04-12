from django.urls import path
from course_catalog_wizard import views

urlpatterns = [
    path("", views.create_session),
    path("<uuid:session_id>/configure/", views.configure),
    path("<uuid:session_id>/commit/", views.commit),
    path("<uuid:session_id>/verify/", views.verify),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
