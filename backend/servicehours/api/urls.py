from django.urls import path
from servicehours.api.views import (
    ServiceEntriesListCreate,
    ServiceStudentSummary,
    ServiceApprovalQueue,
    ServiceApproveReject,
)

urlpatterns = [
    path("entries/", ServiceEntriesListCreate.as_view(), name="service_entries"),
    path("students/<uuid:student_id>/summary/", ServiceStudentSummary.as_view(), name="service_student_summary"),
    path("approvals/", ServiceApprovalQueue.as_view(), name="service_approvals_queue"),
    path("approvals/<uuid:entry_id>/", ServiceApproveReject.as_view(), name="service_approve_reject"),
]

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='api-schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='api-schema'), name='api-docs'),
]
