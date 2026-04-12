from django.urls import path

from . import views

urlpatterns = [
    path("", views.create_session),
    path("<uuid:session_id>/configure/", views.configure_session),
    path("<uuid:session_id>/codes/", views.define_codes),
    path("<uuid:session_id>/commit/", views.commit_session),
    path("<uuid:session_id>/verify/", views.verify_session),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
