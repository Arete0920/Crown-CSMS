from django.urls import path

from .admin_views import sandbox_admin_resolve, sandbox_admin_state
from .finance_views import sandbox_finance_apply_payment, sandbox_finance_state
from .parent_daily_views import sandbox_parent_daily
from .student_views import sandbox_student_self_service
from .views import (
    SandboxCatalogView,
    SandboxEventView,
    SandboxFeedbackView,
    SandboxInviteCreateView,
    SandboxInviteResolveView,
    SandboxInviteRevokeView,
    SandboxParentEnrollmentView,
    SandboxSessionView,
)

urlpatterns = [
    path("catalog/", SandboxCatalogView.as_view(), name="sandbox-catalog"),
    path("session/", SandboxSessionView.as_view(), name="sandbox-session"),
    path("parent/enrollment/", SandboxParentEnrollmentView.as_view(), name="sandbox-parent-enrollment"),
    path("parent/daily/", sandbox_parent_daily, name="sandbox-parent-daily"),
    path("events/", SandboxEventView.as_view(), name="sandbox-events"),
    path("feedback/", SandboxFeedbackView.as_view(), name="sandbox-feedback"),
    path("admin/state/", sandbox_admin_state, name="sandbox-admin-state"),
    path("admin/resolve-operational-exception/", sandbox_admin_resolve, name="sandbox-admin-resolve"),
    path("finance/state/", sandbox_finance_state, name="sandbox-finance-state"),
    path("finance/apply-payment/", sandbox_finance_apply_payment, name="sandbox-finance-apply-payment"),
    path("student/self-service/", sandbox_student_self_service, name="sandbox-student-self-service"),
    path("invites/", SandboxInviteCreateView.as_view(), name="sandbox-invite-create"),
    path("invites/<str:invite_id>/", SandboxInviteResolveView.as_view(), name="sandbox-invite-resolve"),
    path("invites/<str:invite_id>/revoke/", SandboxInviteRevokeView.as_view(), name="sandbox-invite-revoke"),
]
