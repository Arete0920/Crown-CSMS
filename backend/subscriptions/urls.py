from django.urls import path

from . import views

urlpatterns = [
    path("", views.list_school_modules, name="modules-list"),
    path("activate/", views.activate_module, name="modules-activate"),
    path("deactivate/", views.deactivate_module, name="modules-deactivate"),
    path("trial/", views.start_trial, name="modules-trial"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
