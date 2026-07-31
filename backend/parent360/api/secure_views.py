from __future__ import annotations

import logging
from typing import Any

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from parent360.identity import Parent360IdentityError, resolve_household_for_account

from .views import (
    _build_admissions_continuity,
    _build_child_overview_row,
    _get_children_for_household,
    _get_household_balance_cents,
)

logger = logging.getLogger(__name__)


class ParentSelfOverview(APIView):
    """Parent360 overview authorized only by the canonical account link."""

    permission_classes = [IsAuthenticated]

    def get(self, request: Any):
        try:
            household = resolve_household_for_account(request.user)
        except Parent360IdentityError as exc:
            logger.warning(
                "parent360 identity resolution denied",
                extra={
                    "parent360_identity_code": str(exc),
                    "user_id": str(getattr(request.user, "pk", "")),
                    "school_id": str(getattr(request.user, "school_id", "")),
                },
            )
            return Response(
                {"detail": "No active household access is configured for the current account."},
                status=status.HTTP_404_NOT_FOUND,
            )

        children = _get_children_for_household(household)

        grade_entry_model = None
        assignment_model = None
        enrollment_model = None
        invoice_model = None
        invoice_line_model = None
        service_entry_model = None

        try:
            from gradebook.models import GradeEntry as grade_entry_model
            from academics.models import Assignment as assignment_model, Enrollment as enrollment_model
        except Exception:
            logger.exception("parent360 gradebook or academics imports unavailable")

        try:
            from billing.models import Invoice as invoice_model, InvoiceLine as invoice_line_model
        except Exception:
            logger.exception("parent360 billing imports unavailable")

        try:
            from servicehours.models import ServiceEntry as service_entry_model
        except Exception:
            logger.exception("parent360 service-hours imports unavailable")

        now = timezone.now().date()
        seven_days = now + timezone.timedelta(days=7)
        household_balance_cents = _get_household_balance_cents(
            household,
            invoice_model,
            invoice_line_model,
        )

        child_rows = []
        missing_total = 0
        upcoming_total = 0

        for student in children:
            school_id = getattr(student, "school_id", None)
            row, missing_delta, upcoming_delta = _build_child_overview_row(
                student,
                grade_entry_model,
                assignment_model,
                enrollment_model,
                invoice_model,
                invoice_line_model,
                service_entry_model,
                school_id,
                now,
                seven_days,
            )
            child_rows.append(row)
            missing_total += missing_delta
            upcoming_total += upcoming_delta

        payload = {
            "household": {
                "id": str(getattr(household, "id")),
                "name": getattr(household, "name", ""),
                "balance_cents": household_balance_cents,
            },
            "children_count": len(child_rows),
            "missing_assignments_total": missing_total,
            "upcoming_assignments_total": upcoming_total,
            "children": child_rows,
            "admissions_continuity": _build_admissions_continuity(household),
        }

        return Response(payload, status=status.HTTP_200_OK)
