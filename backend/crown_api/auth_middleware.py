# backend/crown_api/auth_middleware.py
import json
from uuid import UUID

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from audit.models import AuditLog
from core.models import UserRole
from crown_api.director_views import ALLOWED_ROLE_CODES
from crown_api.jwt_utils import decode_access, _b64url_decode
from crown_api.auth_models import CrownUser


MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _is_crown_access_token(token: str) -> bool:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return