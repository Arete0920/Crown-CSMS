"""Strict, entitled director-only setup with canonical GET readback."""
from django.core.exceptions import ValidationError as ModelValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .daycare_api import _staff_scope, _strict_payload
from .daycare_models import DaycareSite, DaycareRoom
from .daycare_setup import ConfigurationConflict, create_configuration, require_configuration


class SiteInput(serializers.Serializer):
    code = serializers.SlugField(max_length=48)
    name = serializers.CharField(max_length=160)
    operating_mode = serializers.ChoiceField(choices=["STANDALONE", "INTEGRATED"])
    jurisdiction = serializers.ChoiceField(choices=["US-DE"])


class RoomInput(serializers.Serializer):
    code = serializers.SlugField(max_length=48)
    name = serializers.CharField(max_length=160)
    licensed_capacity = serializers.IntegerField(min_value=1, allow_null=True, default=None)
    max_children_per_staff = serializers.IntegerField(min_value=1, allow_null=True, default=None)
    policy_source = serializers.CharField(max_length=255, allow_blank=True, default="")
    proposed_min_age_months = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    proposed_max_age_months = serializers.IntegerField(min_value=0, allow_null=True, default=None)
    proposed_policy_from = serializers.DateField(allow_null=True, default=None)
    proposed_policy_until = serializers.DateField(allow_null=True, default=None)


def room_data(room):
    return {"room_id": str(room.pk), **RoomInput(room).data,
            "is_active": room.is_active,
            "policy_verified_at": room.policy_verified_at.isoformat() if room.policy_verified_at else None}


def site_data(site):
    return {"site_id": str(site.pk), "code": site.code, "name": site.name,
            "operating_mode": site.operating_mode, "jurisdiction": site.jurisdiction,
            "is_active": site.is_active}


def _create(request, school, serializer, site_id=None):
    values = _strict_payload(request, serializer)
    try:
        record, created = create_configuration(
            school_id=school.pk, actor_id=request.user.pk, values=values, site_id=site_id,
        )
    except ConfigurationConflict:
        return Response({"detail": "Code already belongs to different configuration."}, status=409)
    except ModelValidationError:
        return Response({"detail": "Configuration values are inconsistent."}, status=400)
    return Response(room_data(record) if site_id else site_data(record), status=201 if created else 200)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def setup_sites(request):
    school = _staff_scope(request, "diadem.daycare.configure")
    if request.method == "POST":
        return _create(request, school, SiteInput)
    with transaction.atomic():
        require_configuration(school.pk, request.user.pk)
        sites = DaycareSite.objects.filter(school=school).order_by("name", "pk")
        return Response({"school_id": str(school.pk), "as_of": timezone.now().isoformat(),
                         "source": "aftercare.DaycareSite", "sites": [site_data(s) for s in sites]})


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def setup_rooms(request, site_id):
    school = _staff_scope(request, "diadem.daycare.configure")
    if request.method == "POST":
        return _create(request, school, RoomInput, site_id)
    with transaction.atomic():
        require_configuration(school.pk, request.user.pk)
        site = DaycareSite.objects.filter(pk=site_id, school=school).first()
        if site is None:
            from rest_framework.exceptions import NotFound
            raise NotFound()
        rooms = DaycareRoom.objects.filter(school=school, site=site).order_by("name", "pk")
        return Response({"school_id": str(school.pk), "site_id": str(site.pk),
                         "as_of": timezone.now().isoformat(), "source": "aftercare.DaycareRoom",
                         "rooms": [room_data(r) for r in rooms]})
