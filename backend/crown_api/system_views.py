from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser

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
