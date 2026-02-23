from decimal import Decimal
from django.db.models import Sum, Count, Case, When, Value, IntegerField
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.permissions import user_has_permission
from .models import FinancialAidApplication, AidAward, AidBucket
from .tenant import require_school_id

class FinancialAidSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = getattr(request, "school", None)
        if not user_has_permission(request.user, "financial_aid.view", school=school):
            return Response({"detail": "Permission denied."}, status=403)
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

        # Awards by bucket (frozen contract uses "total" not "count")
        awards_by_bucket = {}
        for key, label in AidBucket.choices:
            bucket_agg = awards_qs.filter(bucket=key).aggregate(
                count=Count("id"),
                amount=Sum("amount")
            )
            awards_by_bucket[key] = {
                "total": bucket_agg["count"] or 0,
                "amount": str(bucket_agg["amount"] or Decimal("0.00")),
            }

        # Build response contract (frozen)
        payload = {
            "academic_year": academic_year,
            "applications": {
                "total": applications_total,
                "by_status": {
                    "draft": apps_by_status["draft"],
                    "submitted": apps_by_status["submitted"],
                    "in_review": apps_by_status["in_review"],
                    "decided": apps_by_status["decided"],
                },
            },
            "awards": {
                "total": awards_total_count,
                "total_amount": str(awards_total_amount),
                "avg_amount": str(avg_award_amount),
                "by_bucket": awards_by_bucket,
            },
        }

        return Response(payload)

class FinancialAidDrilldownView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = getattr(request, "school", None)
        if not user_has_permission(request.user, "financial_aid.view", school=school):
            return Response({"detail": "Permission denied."}, status=403)
        # Rationale is sensitive — only visible to holders of financial_aid.view_rationale
        can_see_rationale = user_has_permission(
            request.user, "financial_aid.view_rationale", school=school
        )
        school_id = require_school_id(request)
        academic_year = request.query_params.get("academic_year")
        bucket = request.query_params.get("bucket")  # optional

        # If academic_year not provided, use latest year for this school
        if not academic_year:
            latest_app = FinancialAidApplication.objects.filter(
                school_id=school_id
            ).order_by("-academic_year").values_list("academic_year", flat=True).first()
            academic_year = latest_app or "2025-2026"

        # Validate bucket parameter
        valid_buckets = [key for key, label in AidBucket.choices]
        if bucket and bucket not in valid_buckets:
            return Response(
                {"detail": f"Invalid bucket '{bucket}'. Must be one of: {', '.join(valid_buckets)}"},
                status=400
            )

        # Parse pagination params
        try:
            limit = int(request.query_params.get("limit", 25))
            offset = int(request.query_params.get("offset", 0))
        except (ValueError, TypeError):
            return Response({"detail": "limit and offset must be integers"}, status=400)

        # Validate pagination bounds
        if limit < 1 or limit > 200:
            return Response({"detail": "limit must be between 1 and 200"}, status=400)
        if offset < 0:
            return Response({"detail": "offset must be >= 0"}, status=400)

        # Base queryset
        qs = AidAward.objects.filter(
            school_id=school_id,
            application__isnull=False,
            application__academic_year=academic_year
        ).select_related("application").order_by("-created_at", "id")

        # Apply bucket filter if provided
        if bucket:
            qs = qs.filter(bucket=bucket)

        # Count total before pagination
        total_count = qs.count()

        # Apply pagination
        page = qs[offset:offset+limit]

        # Build rows with stable schema
        rows = []
        for a in page:
            application_status = a.application.status if a.application else None
            if application_status == "decided":
                award_status = "awarded" if a.amount and a.amount > 0 else "denied"
            else:
                award_status = "revised"
            rows.append(
                {
                    "award_id": str(a.id),
                    "application_id": str(a.application_id) if a.application_id else None,
                    "household_id": str(a.application.household_id) if a.application and a.application.household_id else None,
                    "bucket": a.bucket,
                    "amount": str(a.amount),
                    "application_status": application_status,
                    "award_status": award_status,
                    "rationale": (a.rationale if a.rationale else None) if can_see_rationale else None,
                    "updated_at": a.updated_at.isoformat() if a.updated_at else None,
                }
            )

        return Response(
            {
                "academic_year": academic_year,
                "bucket": bucket,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "rows": rows,
            }
        )
