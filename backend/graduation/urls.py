from django.urls import path
from .views import GraduationAuditView
from .views_breakdown import GraduationAuditBreakdownView

urlpatterns = [
    path("audit/<uuid:student_id>/", GraduationAuditView.as_view(), name="graduation-audit"),
    path("audit/<uuid:student_id>/breakdown/", GraduationAuditBreakdownView.as_view(), name="graduation-audit-breakdown"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
