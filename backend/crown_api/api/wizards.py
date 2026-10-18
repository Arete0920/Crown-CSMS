"""
GET /api/v1/wizards/   — Wizard discovery endpoint.

Returns the ordered list of all registered wizards so the frontend can
stay aligned with the backend registry without manual slug lists.

Auth: JWTAuthentication (same guardrail as every wizard session endpoint).
"""
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.response import Response

from crown_api.wizard_registry import list_wizards

_AUTH = [JWTAuthentication, SessionAuthentication]
_PERM = [IsAuthenticated]


@api_view(["GET"])
@authentication_classes(_AUTH)
@permission_classes(_PERM)
def wizard_discovery(request):
    # This response is generated from the active backend wizard registry at
    # request time. Preserve explicit provenance so production certification
    # can distinguish the live registry from frontend fallback or sample data.
    return Response(
        {
            "wizards": list_wizards(),
            "meta": {"served_from": "live"},
        }
    )
