from django.urls import path

from .admin_views import sandbox_admin_resolve, sandbox_admin_state
from .finance_views import sandbox_finance_apply_payment, sandbox_finance_state
from .views import (
    SandboxCatalogView,
    SandboxEventView,
    SandboxFeedbackView,
    SandboxInviteCreateView,
    SandboxInviteResolveView,
    SandboxInviteRevokeView,
    SandboxSessionView,
)

urlpatterns = [
    path("catalog/", SandboxCatalogView.as_view(), name="sandbox-catalog"),
    path("session/", SandboxSessionView.as_view(), name="sandbox-session"),
    path("events/", SandboxEventView.as_view(), name="sandbox-events"),
    path("feedback/", SandboxFeedbackView.as_view(), name="sandbox-feedback"),
    path("admin/state/", sandbox_admin_state, name="sandbox-admin-state"),
    path("admin/resolve-operational-exception/", sandbox_admin_resolve, name="sandbox-admin-resolve"),
    path("finance/state/", sandbox_finance_state, name="sandbox-finance-state"),
    path("finance/apply-payment/", sandbox_finance_apply_payment, name="sandbox-finance-apply-payment"),
    path("invites/", SandboxInviteCreateView.as_view(), name="sandbox-invite-create"),
    path("invites/<str:invite_id>/", SandboxInviteResolveView.as_view(), name="sandbox-invite-resolve"),
    path("invites/<str:invite_id>/revoke/", SandboxInviteRevokeView.as_view(), name="sandbox-invite-revoke"),
]
