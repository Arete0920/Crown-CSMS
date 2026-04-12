from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="student_import_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="student_import_wizard_configure"),
    path("<uuid:session_id>/preview/", views.preview_session, name="student_import_wizard_preview"),
    path("<uuid:session_id>/commit/", views.commit_session, name="student_import_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="student_import_wizard_verify"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
