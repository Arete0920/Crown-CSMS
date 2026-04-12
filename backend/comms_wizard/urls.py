from django.urls import path

from . import views

urlpatterns = [
    path("", views.create_session, name="comms_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="comms_wizard_configure"),
    path("<uuid:session_id>/message/", views.draft_message, name="comms_wizard_message"),
    path("<uuid:session_id>/recipients/", views.stage_recipients, name="comms_wizard_recipients"),
    path("<uuid:session_id>/commit/", views.commit_session, name="comms_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="comms_wizard_verify"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
