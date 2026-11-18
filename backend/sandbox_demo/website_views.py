"""Public launcher for one owned fictional DEV school; no customer access."""
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog import SANDBOX_PERSONAS
from .website_presenter import (
    DEMO_ORIGIN, issue_website_demo_session, website_demo_rate_limit,
    website_demo_school,
)


class WebsitePresenterEntryView(APIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def _response(self, data, status=200):
        response = Response(data, status=status)
        response["Cache-Control"] = "no-store, private"
        return response

    def get(self, request):
        school = website_demo_school()
        if school is None:
            return self._response({
                "available": False, "code": "website_presenter_not_ready",
            }, status=503)
        return self._response({
            "available": True,
            "school": {"id": str(school.pk), "name": school.name},
            "roles": [{"key": key, "label": persona.label}
                      for key, persona in SANDBOX_PERSONAS.items()],
        })

    def post(self, request):
        # A cross-origin static-app POST must originate from the exact owned
        # DEV preview. No public session fallback, reusable invite, or cookies.
        if request.headers.get("Origin") != DEMO_ORIGIN:
            return self._response({
                "detail": "Demonstration origin not permitted.",
                "code": "website_presenter_origin_denied",
            }, status=403)
        if not website_demo_rate_limit(request):
            return self._response({
                "detail": "Demonstration entry rate limited.",
                "code": "website_presenter_rate_limited",
            }, status=429)
        school = website_demo_school()
        if school is None:
            return self._response({
                "detail": "The fictional school is not ready.",
                "code": "website_presenter_not_ready",
            }, status=503)
        role = request.data.get("role") if isinstance(request.data, dict) else None
        if not isinstance(role, str) or role not in SANDBOX_PERSONAS:
            return self._response({
                "detail": "Unknown presenter role.",
                "code": "website_presenter_role_invalid",
            }, status=400)
        try:
            session = issue_website_demo_session(school, role)
        except Exception:
            return self._response({
                "detail": "Presenter role is unavailable.",
                "code": "website_presenter_role_unavailable",
            }, status=503)
        return self._response(session, status=201)
