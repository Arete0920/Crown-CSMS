"""Explicit SGO-organization authorization for the isolated, pilot-only API."""
from django.http import Http404
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import SGOApplication, SGOAward, SGOMembership, SGOProgram
from .services import (
    membership_for, create_program, create_application, attest_eligibility, commit_award,
)


def reject_school_header(request):
    """A school tenant selector can never act as grantor authorization."""
    if request.headers.get("X-School-Id") or request.headers.get("X-Crown-School-Id"):
        raise ValidationError({"detail": "School tenant headers are not accepted on SGO routes."})


def payload(request):
    if not isinstance(request.data, dict):
        raise ValidationError({"detail": "A JSON object is required."})
    return request.data


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def programs(request, organization_id):
    reject_school_header(request)
    membership_for(request.user, organization_id)
    if request.method == "GET":
        records = SGOProgram.objects.filter(organization_id=organization_id).order_by("code", "calendar_year")
        return Response({"results": [
            {
                "id": str(item.id), "name": item.name, "code": item.code,
                "calendar_year": item.calendar_year, "funding_source": item.funding_source,
                "eligibility_rule_version": item.eligibility_rule_version, "status": item.status,
            }
            for item in records[:200]
        ]})
    data = payload(request)
    year = data.get("calendar_year")
    if type(year) is not int:
        raise ValidationError({"calendar_year": "An integer year is required."})
    item = create_program(
        user=request.user, organization_id=organization_id,
        name=data.get("name"), code=data.get("code"),
        calendar_year=year, funding_source=data.get("funding_source"),
        rule_version=data.get("eligibility_rule_version"),
    )
    return Response({"id": str(item.id), "status": item.status}, status=status.HTTP_201_CREATED)


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def applications(request, organization_id):
    reject_school_header(request)
    membership_for(request.user, organization_id)
    if request.method == "GET":
        records = SGOApplication.objects.filter(
            organization_id=organization_id, program__organization_id=organization_id
        ).order_by("-created_at")
        return Response({"results": [
            {
                "id": str(item.id), "program_id": str(item.program_id),
                "student_key": str(item.student_key), "school_key": str(item.school_key),
                "eligibility": item.eligibility,
            }
            for item in records[:200]
        ]})
    data = payload(request)
    item = create_application(
        user=request.user, organization_id=organization_id,
        program_id=data.get("program_id"), student_key=data.get("student_key"),
        school_key=data.get("school_key"),
    )
    return Response({"id": str(item.id), "eligibility": item.eligibility},
                    status=status.HTTP_201_CREATED)


@api_view(["POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def review(request, organization_id, application_id):
    reject_school_header(request)
    data = payload(request)
    item = attest_eligibility(
        user=request.user, organization_id=organization_id, application_id=application_id,
        eligible=data.get("eligible"), evidence_key=data.get("evidence_key"),
    )
    return Response({"id": str(item.id), "eligibility": item.eligibility})


@api_view(["GET", "POST"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def awards(request, organization_id):
    reject_school_header(request)
    membership_for(request.user, organization_id)
    if request.method == "GET":
        records = SGOAward.objects.filter(
            organization_id=organization_id, application__organization_id=organization_id,
            application__program__organization_id=organization_id,
        ).order_by("-committed_at")
        return Response({"results": [
            {
                "id": str(item.id), "application_id": str(item.application_id),
                "amount_cents": item.amount_cents, "status": item.status,
            }
            for item in records[:200]
        ]})
    data = payload(request)
    item = commit_award(
        user=request.user, organization_id=organization_id,
        application_id=data.get("application_id"), amount_cents=data.get("amount_cents"),
    )
    return Response({
        "id": str(item.id), "status": item.status, "amount_cents": item.amount_cents,
        "cash_movement": False,
    }, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def summary(request, organization_id):
    reject_school_header(request)
    membership_for(request.user, organization_id)
    return Response({
        "programs": SGOProgram.objects.filter(organization_id=organization_id).count(),
        "applications": SGOApplication.objects.filter(
            organization_id=organization_id, program__organization_id=organization_id
        ).count(),
        "commitments": SGOAward.objects.filter(
            organization_id=organization_id, application__organization_id=organization_id,
            application__program__organization_id=organization_id,
        ).count(),
        "cash_disbursed_cents": None,
        "live_settlement_enabled": False,
        "regulatory_certified": False,
    })
