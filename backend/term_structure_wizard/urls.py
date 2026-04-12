from django.urls import path

from . import views

urlpatterns = [
    path("",                          views.create_session,    name="ts-create"),
    path("<uuid:session_id>/configure/", views.configure_session, name="ts-configure"),
    path("<uuid:session_id>/periods/",   views.set_periods,       name="ts-periods"),
    path("<uuid:session_id>/commit/",    views.commit_session,    name="ts-commit"),
    path("<uuid:session_id>/verify/",    views.verify_session,    name="ts-verify"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
