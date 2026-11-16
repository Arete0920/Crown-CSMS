"""Explicit-permission Diadem evidence review API: no activation endpoints."""
import re

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .daycare_api import _staff_scope, _strict_payload
from .daycare_approval import (
    SafetyReviewConflict, list_reviews,
    submit_assignment, submit_policy, submit_qualification,
)


class ReviewInput(serializers.Serializer):
    source_authority = serializers.CharField(max_length=160, trim_whitespace=True)
    source_reference = serializers.CharField(max_length=255, trim_whitespace=True)
    effective_from = serializers.DateTimeField()
    effective_until = serializers.DateTimeField()
    decision = serializers.CharField()
    request_key = serializers.UUIDField()
    supersedes_id = serializers.UUIDField(required=False, allow_null=True)

    def validate(self, values):
        for name in ("effective_from", "effective_until"):
            raw = self.initial_data.get(name)
            if not isinstance(raw, str) or not re.search(
                r"(?:Z|[+-][0-9]{2}:[0-9]{2})$", raw, re.IGNORECASE,
            ):
                raise serializers.ValidationError({name: "Explicit UTC offset required."})
        if values["effective_from"] >= values["effective_until"]:
            raise serializers.ValidationError({"effective_until": "End must follow start."})
        return values


class QualificationInput(ReviewInput):
    staff_id = serializers.UUIDField()
    qualification_code = serializers.CharField(max_length=64, trim_whitespace=True)
    decision = serializers.ChoiceField(choices=["VERIFIED", "REJECTED", "REVOKED"])


class RoomPolicyInput(ReviewInput):
    jurisdiction = serializers.CharField(max_length=16)
    policy_version = serializers.CharField(max_length=64)
    facility_license_reference = serializers.CharField(max_length=160)
    age_min_months = serializers.IntegerField(min_value=0)
    age_max_months = serializers.IntegerField(min_value=0)
    licensed_capacity = serializers.IntegerField(min_value=1)
    max_group_size = serializers.IntegerField(min_value=1)
    max_children_per_staff = serializers.IntegerField(min_value=1)
    decision = serializers.ChoiceField(choices=["APPROVED", "REJECTED", "REVOKED"])

    def validate(self, values):
        values = super().validate(values)
        if values["age_min_months"] > values["age_max_months"]:
            raise serializers.ValidationError({"age_max_months": "Age band must be ordered."})
        return values


class AssignmentInput(ReviewInput):
    proposal_id = serializers.UUIDField()
    qualification_review_id = serializers.UUIDField()
    room_policy_review_id = serializers.UUIDField()
    decision = serializers.ChoiceField(choices=["APPROVED", "REJECTED", "REVOKED"])


def _submit(request, site_id, room_id, serializer, submitter):
    school = _staff_scope(request, "diadem.daycare.configure")
    values = _strict_payload(request, serializer)
    try:
        review, created = submitter(
            school_id=school.pk, actor_id=request.user.pk,
            site_id=site_id, room_id=room_id, values=values,
        )
    except SafetyReviewConflict:
        return Response({"detail": "Safety review conflicts with existing evidence."}, status=409)
    return Response({
        "review_id": str(review.pk), "decision": review.decision,
        "operational_activation": False,
    }, status=201 if created else 200)


@extend_schema(methods=["GET"], responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def safety_review_readback(request, site_id, room_id):
    school = _staff_scope(request, "diadem.daycare.configure")
    return Response(list_reviews(
        school_id=school.pk, actor_id=request.user.pk,
        site_id=site_id, room_id=room_id,
    ))


@extend_schema(methods=["POST"], request=QualificationInput, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def qualification_review(request, site_id, room_id):
    return _submit(request, site_id, room_id, QualificationInput, submit_qualification)


@extend_schema(methods=["POST"], request=RoomPolicyInput, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def room_policy_review(request, site_id, room_id):
    return _submit(request, site_id, room_id, RoomPolicyInput, submit_policy)


@extend_schema(methods=["POST"], request=AssignmentInput, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assignment_review(request, site_id, room_id):
    return _submit(request, site_id, room_id, AssignmentInput, submit_assignment)
