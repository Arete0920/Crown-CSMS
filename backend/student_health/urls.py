from django.urls import path
from .api import health_workspace

urlpatterns = [path('workspace/', health_workspace, name='student-health-workspace')]
