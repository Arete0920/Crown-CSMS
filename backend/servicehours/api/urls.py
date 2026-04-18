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
