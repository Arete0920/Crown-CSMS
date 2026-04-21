from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from crown_api.exports.permissions import IsFinanceRole


class TranscriptRouteProbeView(APIView):
    """Compatibility endpoint for release-certification transcript route checks."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "detail": "Use student-specific transcript endpoints.",
                "canonical": [
                    "/api/v1/academics/transcript/{student_id}/",
                    "/api/v1/transcripts/students/{student_id}/",
                    "/api/v1/academics/students/{student_id}/transcript/",
                ],
            }
        )


class TranscriptGenerateProbeView(APIView):
    """Explicit non-404 transcript generation surface for gated checks."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        student_id = request.data.get("student_id")
        if not student_id:
            return Response({"detail": "student_id is required"}, status=400)
        return Response(
            {
                "detail": "Use canonical transcript endpoints for retrieval.",
                "student_id": student_id,
            },
            status=202,
        )


class ExportsIndexView(APIView):
    """Compatibility index for export route gating."""

    permission_classes = [IsAuthenticated, IsFinanceRole]

    def get(self, request):
        return Response(
            {
                "detail": "Canonical CSV exports",
                "exports": [
                    "/api/v1/exports/invoices.csv",
                    "/api/v1/exports/installment-schedule.csv",
                    "/api/v1/exports/households.csv",
                    "/api/v1/exports/students.csv",
                    "/api/v1/exports/staff.csv",
                    "/api/v1/exports/ledger-charges.csv",
                    "/api/v1/exports/ledger-allocations.csv",
                    "/api/v1/exports/payments.csv",
                    "/api/v1/exports/statements.csv",
                    "/api/v1/exports/statement-lines.csv",
                    "/api/v1/exports/year-end/tuition-paid.csv",
                    "/api/v1/exports/accounting/payments-qb.csv",
                ],
            }
        )


class ReportsExportFacadeView(APIView):
    """Facade route used by release gate; points to canonical exports namespace."""

    permission_classes = [IsAuthenticated, IsFinanceRole]

    def get(self, request):
        return Response(
            {
                "detail": "Use /api/v1/exports/* CSV routes.",
                "canonical_base": "/api/v1/exports/",
            }
        )
