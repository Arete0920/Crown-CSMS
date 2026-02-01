import os
from django.core.management import call_command
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework import status

from core.models_seed import SeedRun


class SeedStatusView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        runs = SeedRun.objects.all()[:10]
        return Response(
            {
                "runs": [
                    {
                        "created_at": r.created_at.isoformat(),
                        "env_name": r.env_name,
                        "build_sha": r.build_sha,
                        "school_id": str(r.school_id) if r.school_id else None,
                        "command": r.command,
                        "force": r.force,
                        "status": r.status,
                        "summary": r.summary_json,
                        "error": r.error_text,
                    }
                    for r in runs
                ]
            }
        )


class DemoResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        secret = request.headers.get("X-Ops-Secret", "") or request.headers.get("X-Demo-Reset-Secret", "")
        expected = (
            os.getenv("OPS_RESET_SECRET", "")
            or os.getenv("DEV_OPS_SECRET", "")
            or os.getenv("DEMO_RESET_SECRET", "")
        )

        if not expected:
            return Response(
                {"error": "Server not configured for demo reset"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if secret != expected:
            return Response(
                {"error": "Invalid or missing X-Ops-Secret header"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        school_id = request.data.get("school_id")
        if not school_id:
            return Response(
                {"error": "school_id required in request body"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            call_command("migrate", "--noinput")
            call_command("golden_path_bootstrap", "--force", f"--school-id={school_id}", "--verbosity=2")
            latest_run = SeedRun.objects.order_by("-created_at").first()
            
            if latest_run:
                return Response({
                    "status": "success",
                    "seed_run": {
                        "created_at": latest_run.created_at.isoformat(),
                        "env_name": latest_run.env_name,
                        "build_sha": latest_run.build_sha,
                        "school_id": str(latest_run.school_id) if latest_run.school_id else None,
                        "command": latest_run.command,
                        "force": latest_run.force,
                        "status": latest_run.status,
                        "summary": latest_run.summary_json,
                        "error": latest_run.error_text,
                    }
                })
            else:
                return Response({"status": "success", "message": "Command executed but no SeedRun found"})
                
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
