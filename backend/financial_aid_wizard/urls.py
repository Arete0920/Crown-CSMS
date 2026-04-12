from django.urls import path
from . import views

urlpatterns = [
    path("", views.create_session, name="aid_wizard_create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="aid_wizard_configure"),
    path("<uuid:session_id>/buckets/", views.save_buckets, name="aid_wizard_buckets"),
    path("<uuid:session_id>/awards/", views.stage_awards, name="aid_wizard_awards"),
    path("<uuid:session_id>/commit/", views.commit_session, name="aid_wizard_commit"),
    path("<uuid:session_id>/verify/", views.verify_session, name="aid_wizard_verify"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
