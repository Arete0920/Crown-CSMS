"""
URL configuration for crown_api project.
"""
from django.urls import include, path
from django.views.generic import RedirectView
from crown_api.views import director_dashboard_page, director_router

urlpatterns = [
    path("", RedirectView.as_view(url="director/", permanent=False)),
    path("api/", include("crown_api.api_urls")),
    
    # Director routing - persona-specific URLs all use same view
    path("director/", director_router, name="director_router"),
    path("director/aid/", director_dashboard_page, {'persona': 'aid'}, name="director_aid"),
    path("director/admissions/", director_dashboard_page, {'persona': 'admissions'}, name="director_admissions"),
    path("director/finance/", director_dashboard_page, {'persona': 'finance'}, name="director_finance"),
    path("director/registrar/", director_dashboard_page, {'persona': 'registrar'}, name="director_registrar"),
]

# Admin URLs added after app initialization
try:
    from django.contrib.admin import site
    urlpatterns.append(path("admin/", site.urls))
except Exception:
    pass
