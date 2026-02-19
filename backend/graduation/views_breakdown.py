# backend/graduation/views_breakdown.py

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class GraduationAuditBreakdownView(APIView):
    """
    GET /api/v1/graduation/audit/<student_uuid>/breakdown/
    - In DEMO_MODE: returns deterministic, investor-friendly breakdown (no DB required)
    - In non-demo: tries to reuse an existing audit service if present; otherwise returns 501
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        demo_mode = bool(getattr(settings, "CROWN_DEMO_MODE", False))

        if demo_mode:
            # Deterministic demo payload (no migrations / no DB dependency)
            # Keep it consistent and "plausible" for the drawer.
            payload = {
                "student_id": str(student_id),
                "as_of": "2026-02-19T20:15:00Z",
                "credits": {"earned": 19.5, "required": 24.0},
                "status": "ON_TRACK",
                "requirements": [
                    {"name": "English", "required": 4.0, "earned": 3.0, "met": False},
                    {"name": "Math", "required": 3.0, "earned": 3.0, "met": True},
                    {"name": "Science", "required": 3.0, "earned": 2.0, "met": False},
                    {"name": "History", "required": 3.0, "earned": 3.0, "met": True},
                    {"name": "Bible/Theology", "required": 4.0, "earned": 4.0, "met": True},
                    {"name": "Foreign Language", "required": 2.0, "earned": 1.0, "met": False},
                    {"name": "Fine Arts", "required": 1.0, "earned": 1.0, "met": True},
                    {"name": "PE/Health", "required": 1.0, "earned": 1.0, "met": True},
                    {"name": "Electives", "required": 3.0, "earned": 1.5, "met": False},
                ],
                "notes": [
                    "Missing 1.0 English credit",
                    "Missing 1.0 Science credit",
                    "Missing 1.0 Foreign Language credit",
                    "Missing 1.5 Electives credits",
                ],
            }
            return Response(payload, status=200)

        # Non-demo path: attempt to reuse your existing audit logic if it exists.
        # This avoids guessing your internal model names. If not present, we fail clearly.
        try:
            from graduation.services import build_graduation_breakdown  # type: ignore
        except Exception:
            return Response(
                {
                    "detail": "Breakdown service not wired (non-demo). DEMO_MODE works. "
                              "Add graduation.services.build_graduation_breakdown(student_id, request)."
                },
                status=501,
            )

        payload = build_graduation_breakdown(student_id=student_id, request=request)
        return Response(payload, status=200)
