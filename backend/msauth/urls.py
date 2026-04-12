from django.urls import path
from .views import (
    microsoft_login,
    microsoft_callback,
    logout_view,
    me_view,
)

urlpatterns = [
    path("microsoft/login/", microsoft_login, name="microsoft_login"),
    path("microsoft/callback/", microsoft_callback, name="microsoft_callback"),
    path("logout/", logout_view, name="sso_logout"),
    path("me/", me_view, name="sso_me"),
]
