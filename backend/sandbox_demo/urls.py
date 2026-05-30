from django.urls import path

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
    path("invites/", SandboxInviteCreateView.as_view(), name="sandbox-invite-create"),
    path("invites/<str:invite_id>/", SandboxInviteResolveView.as_view(), name="sandbox-invite-resolve"),
    path("invites/<str:invite_id>/revoke/", SandboxInviteRevokeView.as_view(), name="sandbox-invite-revoke"),
]
