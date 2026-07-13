# backend/crown_api/auth_middleware.py
import json
from uuid import UUID

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from audit.models import AuditLog
from core.models import UserRole
from crown_api.jwt_utils import decode_access, _b64url_decode