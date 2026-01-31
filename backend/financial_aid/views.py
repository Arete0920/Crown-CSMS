from decimal import Decimal
from django.db.models import Sum, Count, Case, When, Value, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import FinancialAidApplication, AidAward, AidBucket
from .tenant import require_school_id

class FinancialAidSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = require_school_id(request)
        academic_year = request.query_params.get("academic_year")

        # If academic_year not provided, use latest year for this school
        if not academic_year:
            latest_app = FinancialAidApplication.objects.filter(
                school_id=school_id
            ).order_by("-academic_year").values_list("academic_year", flat=True).first()
            academic_year = latest_app or "2025-2026"

        # Fetch applications for this school and year
        apps_qs = FinancialAidApplication.objects.filter(
            school_id=school_id,
            academic_year=academic_year
        )

        # Count applications by status (ensure all statuses present)
        apps_by_status = apps_qs.aggregate(
            draft=Count(Case(When(status="draft", then=1), output_field=IntegerField())),
            submitted=Count(Case(When(status="submitted", then=1), output_field=IntegerField())),
            in_review=Count(Case(When(status="in_review", then=1), output_field=IntegerField())),
            decided=Count(Case(When(status="decided", then=1), output_field=IntegerField())),
        )

        applications_total = apps_qs.count()

        # Fetch awards for this school and year (must have application FK)
        awards_qs = AidAward.objects.filter(
            school_id=school_id,
            application__academic_year=academic_year,
            application__isnull=False
        )

        # Calculate total awards
        awards_agg = awards_qs.aggregate(
            total_count=Count("id"),
            total_amount=Sum("amount")
        )
        awards_total_count = awards_agg["total_count"] or 0
        awards_total_amount = awards_agg["total_amount"] or Decimal("0.00")

        # Calculate average award amount
        if awards_total_count > 0:
            avg_award_amount = awards_total_amount / Decimal(awards_total_count)
        else:
            avg_award_amount = Decimal("0.00")

        # Awards by bucket
        awards_by_bucket = {}
        for key, label in AidBucket.choices:
            bucket_agg = awards_qs.filter(bucket=key).aggregate(
                count=Count("id"),
                amount=Sum("amount")
            )
            awards_by_bucket[key] = {
                "count": bucket_agg["count"] or 0,
                "amount": str(bucket_agg["amount"] or Decimal("0.00")),
            }

        # Build response contract
        payload = {
            "academic_year": academic_year,
            "totals": {
                "applications_total": applications_total,
                "applications_by_status": {
                    "draft": apps_by_status["draft"],
                    "submitted": apps_by_status["submitted"],
                    "in_review": apps_by_status["in_review"],
                    "decided": apps_by_status["decided"],
                },
                "awards_total_count": awards_total_count,
                "awards_total_amount": str(awards_total_amount),
                "avg_award_amount": str(avg_award_amount),
            },
            "awards_by_bucket": awards_by_bucket,
        }

        return Response(payload)

class FinancialAidDrilldownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school_id = require_school_id(request)
        academic_year = request.query_params.get("academic_year", "2026-2027")
        bucket = request.query_params.get("bucket")  # optional

        qs = (
            AidAward.objects.filter(school_id=school_id, application__academic_year=academic_year)
            .select_related("application")
            .order_by("-amount")
        )

        if bucket:
            qs = qs.filter(bucket=bucket)

        rows = []
        for a in qs[:200]:
            rows.append(
                {
                    "award_id": str(a.id),
                    "application_id": str(a.application_id),
                    "household_id": str(a.application.household_id),
                    "bucket": a.bucket,
                    "amount": str(a.amount),
                    "status": a.application.status,
                    "submitted_at": a.application.submitted_at.isoformat(),
                    "rationale": a.rationale,
                }
            )

        return Response(
            {
                "academic_year": academic_year,
                "bucket": bucket,
                "count": qs.count(),
                "rows": rows,
            }
        )
