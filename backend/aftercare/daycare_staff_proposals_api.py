"""Director-only, inert staff coverage proposals for standalone Diadem setup.

No endpoint here can approve credentials, activate coverage or affect custody.
"""
import re

from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .daycare_api import _staff_scope, _strict_payload
from .daycare_staff_proposals import (
    StaffProposalConflict, create_staff_proposal, list_staff_proposals,
    staff_proposal_data,
)


class StaffProposalInput(serializers.Serializer):
    staff_id = serializers.UUIDField()
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()

    def validate(self, values):
        for field in ("starts_at", "ends_at"):
            raw = self.initial_data.get(field)
            if not isinstance(raw, str) or not re.search(
                r"(?:Z|[+-][0-9]{2}:[0-9]{2})$", raw, re.IGNORECASE,
            ):
                raise serializers.ValidationError(
                    {field: "An explicit UTC offset is required."}
                )
        if values["starts_at"] >= values["ends_at"]:
            raise serializers.ValidationError(
                {"ends_at": "Proposal end must follow start."}
            )
        return values


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def setup_staff_proposals(request, site_id, room_id):
    school = _staff_scope(request, "diadem.daycare.configure")
    if request.method == "GET":
        return Response(list_staff_proposals(
            school_id=school.pk, actor_id=request.user.pk,
            site_id=site_id, room_id=room_id,
        ))
    values = _strict_payload(request, StaffProposalInput)
    try:
        proposal, created = create_staff_proposal(
            school_id=school.pk, actor_id=request.user.pk,
            site_id=site_id, room_id=room_id, **values,
        )
    except StaffProposalConflict:
        return Response(
            {"detail": "Proposed staff interval conflicts with existing coverage."},
            status=409,
        )
    return Response(
        staff_proposal_data(proposal),
        status=201 if created else 200,
    )
