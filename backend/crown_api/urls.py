"""
URL configuration for crown_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import include, path
from crown_api.views import director_dashboard_page

urlpatterns = [
    path("api/", include("crown_api.api_urls")),
    path("director/", director_dashboard_page, name="director_dashboard_page"),
]

# Admin URLs added after app initialization
# This avoids AppRegistryNotReady errors at import time
try:
    from django.contrib.admin import site
    urlpatterns.append(path("admin/", site.urls))
except Exception:
    # If admin can't be imported at this stage, it will be set up later
    pass
